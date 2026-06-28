"""
modules/chatworkon.py - self-contained client for chatworkon.com / mailapi.chatworkon.com

Independent implementation - does not import or share code with
modules/tempmailq.py or modules/maildax.py, following this project's
per-module isolation convention.

API model (confirmed via HAR capture 2026-06-28 + a live probe against the
real API - see cli_cwo.py for the full write-up of the auth model and quirks):

  - Stateless JWT bearer auth. No cookies, no CSRF - a Cloudflare Worker JSON
    API, NOT the Laravel session model tempmailq/maildax use.
  - POST /api/new_address {"name": alias} -> {"jwt", "address", "password"}.
    The server ALWAYS prefixes alias with "tmp" - always trust the returned
    `address`, never assume it matches what you sent.
  - GET /api/mails?limit=&offset=  (Authorization: Bearer <jwt>)
    -> {"results": [{id, message_id, source, address, raw, metadata,
                      created_at}], "count"}. `raw` is the full RFC822
    message - parsed locally here with the stdlib email package. There is
    no separate "fetch full body" endpoint like tempmailq's /msg/{id}.
  - GET /api/settings (Authorization: Bearer <jwt>) -> {"address", "send_balance"}.
  - No server-side delete/switch endpoint exists. delete_email() below
    mirrors the real web app's local-only "remove mailbox" behavior.
  - Only one receiving domain: chatcloud.site.
"""

import base64
import json
import os
import random
import re
import string
import email as email_lib
from email import policy
from email.header import decode_header
from email.utils import parseaddr
from curl_cffi import requests as curl_requests

API_BASE     = "https://mailapi.chatworkon.com"
SITE_BASE    = "https://mail.chatworkon.com"
IMPERSONATE  = "chrome124"
HTTP_TIMEOUT = 20
DOMAINS      = ["chatcloud.site"]

SESSION_FILE = os.path.join(os.path.dirname(__file__), '..', 'session_chatworkon.json')


# ── raw RFC822 -> display dict ───────────────────────────────────────────────

def _decode_header_value(raw_value) -> str:
    if not raw_value:
        return ""
    parts = decode_header(raw_value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _parse_raw_email(raw: str) -> dict:
    """Parse one RFC822 message into the {sender, subject, time, body, links}
    shape main.py's show_inbox()/show_message() already expect."""
    msg = email_lib.message_from_string(raw, policy=policy.default)

    subject = _decode_header_value(msg.get("Subject", "")) or "(no subject)"
    from_name, from_email = parseaddr(msg.get("From", ""))
    from_name = _decode_header_value(from_name) or from_email or "unknown"
    date = msg.get("Date", "")

    def _get_text(part):
        try:
            return part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")

    text_body, html_body = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            if ctype == "text/plain" and not text_body:
                text_body = _get_text(part)
            elif ctype == "text/html" and not html_body:
                html_body = _get_text(part)
    else:
        ctype = msg.get_content_type()
        body_text = _get_text(msg)
        if ctype == "text/html":
            html_body = body_text
        else:
            text_body = body_text

    if not text_body and html_body:
        text_body = re.sub(r"<[^>]+>", " ", html_body)
        text_body = re.sub(r"\s+", " ", text_body).strip()

    links = re.findall(r'href=["\']([^"\']+)["\']', html_body) if html_body else []

    sender = f"{from_name} <{from_email}>" if from_email and from_name != from_email else (from_email or from_name)

    return {
        "sender":  sender,
        "subject": subject,
        "time":    date,
        "body":    text_body or "(empty)",
        "links":   links,
    }


def _decode_jwt_address_id(jwt: str):
    try:
        payload_b64 = jwt.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64)).get("address_id")
    except Exception:
        return None


# ── Chatworkon class ──────────────────────────────────────────────────────────

class Chatworkon:
    """
    Single-mailbox client for chatworkon.com, mirroring modules/tempmailq.py's
    public surface (get_current_email, refresh_emails, list_history,
    create_email, delete_email, .current_email, .domains) so main.py can
    drive either provider without caring which one it has.

    Initialization order:
      1. Try to restore jwt from session_chatworkon.json, validate with a
         cheap GET /api/mails call.
      2. If that fails: POST /api/new_address for a fresh address.
    """

    def __init__(self, email: str | None = None):
        self.session = curl_requests.Session(impersonate=IMPERSONATE)
        self.session.headers.update({
            "Accept":          "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin":          SITE_BASE,
            "Referer":         SITE_BASE + "/",
        })
        self.domains       = DOMAINS
        self.jwt           = ""
        self.current_email = email
        self.address_id    = None
        self._history       = []   # [{"address": ..., "jwt": ...}, ...]

        if not self._restore():
            self._init(email)

    # ── low-level HTTP ────────────────────────────────────────────────────

    def _post(self, path: str, data: dict) -> tuple[dict, int]:
        resp = self.session.post(API_BASE + path, json=data, timeout=HTTP_TIMEOUT)
        try:
            body = resp.json()
        except Exception:
            body = {}
        if resp.status_code >= 400:
            body.setdefault("error", f"HTTP {resp.status_code}")
        return body, resp.status_code

    def _get_authed(self, path: str) -> tuple[dict, int]:
        headers = {"Authorization": f"Bearer {self.jwt}"} if self.jwt else {}
        resp = self.session.get(API_BASE + path, headers=headers, timeout=HTTP_TIMEOUT)
        try:
            body = resp.json()
        except Exception:
            body = {}
        if resp.status_code >= 400:
            body.setdefault("error", f"HTTP {resp.status_code}")
        return body, resp.status_code

    # ── persistence ───────────────────────────────────────────────────────

    def _save(self):
        data = {
            "jwt":           self.jwt,
            "current_email": self.current_email,
            "address_id":    self.address_id,
            "history":       self._history,
        }
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _restore(self) -> bool:
        if not os.path.exists(SESSION_FILE):
            return False
        try:
            with open(SESSION_FILE) as f:
                data = json.load(f)
        except Exception:
            return False

        jwt = data.get("jwt", "")
        if not jwt:
            return False

        self.jwt           = jwt
        self.current_email = data.get("current_email", self.current_email)
        self.address_id    = data.get("address_id")
        self._history       = data.get("history", [])

        _, status = self._get_authed("/api/mails?limit=1&offset=0")
        if status != 200:
            self.jwt = ""
            return False
        return True

    # ── creation ──────────────────────────────────────────────────────────

    def _init(self, email: str | None):
        if email and "@" in email:
            alias = email.split("@", 1)[0]
        else:
            alias = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        if not self._create(alias):
            raise RuntimeError("chatworkon: could not create an address (POST /api/new_address failed)")

    def _create(self, alias: str) -> bool:
        body, status = self._post("/api/new_address", {"name": alias})
        if status != 200 or "jwt" not in body:
            return False
        self.jwt           = body["jwt"]
        self.current_email = body.get("address", "")
        self.address_id    = _decode_jwt_address_id(self.jwt)
        if self.current_email and self.current_email not in [h["address"] for h in self._history]:
            self._history.append({"address": self.current_email, "jwt": self.jwt})
        self._save()
        return True

    # ── public API (mirrors TempMailQ) ───────────────────────────────────

    def get_current_email(self) -> str:
        return self.current_email or ""

    def refresh_emails(self) -> list[dict]:
        """Poll GET /api/mails. Returns list of {id, sender, subject, time, body, links}."""
        body, status = self._get_authed("/api/mails?limit=20&offset=0")
        if status != 200:
            return []
        out = []
        for m in body.get("results", []):
            parsed = _parse_raw_email(m.get("raw", ""))
            parsed["id"] = m.get("id")
            parsed["time"] = m.get("created_at", parsed["time"])
            out.append(parsed)
        return out

    def list_history(self) -> list[str]:
        """Local history only - this provider has no server-side history list."""
        return [h["address"] for h in self._history]

    def create_email(self, alias: str | None = None, domain: str | None = None) -> str | None:
        """Mint a new address. `domain` is accepted for interface parity with
        TempMailQ but ignored - chatworkon only has one domain (chatcloud.site)
        and the server always prefixes the alias with 'tmp' regardless."""
        if not alias:
            alias = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return self.current_email if self._create(alias) else None

    def delete_email(self) -> str | None:
        """No server-side delete exists for this provider (confirmed live).
        Mirrors the real web app's local-only 'remove mailbox' behavior:
        drop the current address from local history, then mint a fresh one."""
        if self.current_email:
            self._history = [h for h in self._history if h["address"] != self.current_email]
        alias = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return self.current_email if self._create(alias) else None

    def get_settings(self) -> dict:
        """Bonus over TempMailQ's interface - exposes GET /api/settings
        (address + send_balance). Confirmed live to require the same Bearer auth."""
        body, status = self._get_authed("/api/settings")
        return body if status == 200 else {}
