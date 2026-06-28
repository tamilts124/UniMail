#!/usr/bin/env python3
"""
cli_cwo.py - chatworkon.com / mailapi.chatworkon.com client logic for the
unimail.py CLI.

AUTH MODEL (chatworkon.com) - confirmed from HAR capture 2026-06-28 + a live
probe against the real API:

  This site is COMPLETELY different from tempmailq.com/maildax.cc. There is
  no Laravel session, no cookies, no CSRF token at all. It's a Cloudflare
  Worker JSON API secured with a plain, stateless JWT:

    POST /api/new_address   body: {"name": "<alias>"}
        -> {"jwt": "...", "address": "tmp<alias>@chatcloud.site", "password": null}

    GET  /api/mails?limit=&offset=     header: Authorization: Bearer <jwt>
        -> {"results": [{id, message_id, source, address, raw, metadata,
                          created_at}], "count": N}
        `raw` is the FULL RFC822 message (headers + body, possibly multipart).
        There is no separate "fetch full body" endpoint like tempmailq's
        GET /msg/{id} - everything is already in `raw`.

    GET  /api/settings   header: Authorization: Bearer <jwt>
        -> {"address": "...", "send_balance": 0}
        Not used by the captured browser session, but confirmed live: it DOES
        require the same Bearer header (a bare request with no Authorization
        header returns 401), and returns 200 with a body once authed.

  Important quirks confirmed live (not assumptions):
    - The server ALWAYS prefixes whatever `name` you send with "tmp", e.g.
      name="foo" -> address "tmpfoo@chatcloud.site". You cannot get an address
      without that prefix. Always trust the `address` field in the response,
      never the name you sent.
    - On an invalid/garbage JWT, GET /api/mails returns 401 with a
      COMPLETELY EMPTY body (no JSON at all) - error handling here is purely
      status-code based, there is no error message field to read.
    - The JWT payload is just {"address": ..., "address_id": N} with no
      expiry claim, and there's no token-refresh endpoint - if a stored JWT
      ever stops working, the only recovery is minting a brand-new address.
    - There is no server-side delete/switch/change endpoint. The real web
      app's "remove mailbox" / "switch mailbox" features are 100% local
      (browser localStorage) operations with zero network calls behind them.
    - Only one receiving domain exists (chatcloud.site) - no per-request
      domain selection like tempmailq/maildax.

SESSION MODEL:
  Each email_key gets its own in-process curl_cffi Session + cached JWT,
  persisted into the same .unimail_cache.json used by tempmailq/maildax
  entries (each mailbox's dict just has different fields: "jwt" and
  "address_id" instead of "session_cookies"/"xsrf_token"/"meta_token").
"""

import base64
import json
import random
import re
import string
import email as email_lib
from email import policy
from email.header import decode_header
from email.utils import parseaddr
from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, CHATWORKON_BASE, CHATWORKON_API_BASE, IMPERSONATE, HTTP_TIMEOUT

# in-process session pool: email_key -> {"session": Session, "jwt": str}
_cwo_pool: dict[str, dict] = {}


# ── low-level HTTP ───────────────────────────────────────────────────────────

def _cwo_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         CHATWORKON_BASE + "/",
        "Origin":          CHATWORKON_BASE,
    })
    return s


def _cwo_post(s: curl_requests.Session, path: str, data: dict) -> tuple[dict, int]:
    dbg(f"cwo: POST {path} body={data!r}")
    resp = s.post(CHATWORKON_API_BASE + path, json=data, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"cwo: POST {path} -> {resp.status_code}  body={body!r}")
    if resp.status_code >= 400:
        body.setdefault("error", f"HTTP {resp.status_code} (empty body)" if not body else f"HTTP {resp.status_code}")
    return body, resp.status_code


def _cwo_get_authed(s: curl_requests.Session, path: str, jwt: str) -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {jwt}"} if jwt else {}
    dbg(f"cwo: GET {path} (jwt={'set' if jwt else 'MISSING'})")
    resp = s.get(CHATWORKON_API_BASE + path, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"cwo: GET {path} -> {resp.status_code}  body={body!r}")
    if resp.status_code >= 400:
        body.setdefault("error", f"HTTP {resp.status_code} (empty body)" if not body else f"HTTP {resp.status_code}")
    return body, resp.status_code


def _cwo_decode_jwt_address_id(jwt: str):
    try:
        payload_b64 = jwt.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64)).get("address_id")
    except Exception:
        return None


# ── email-address-quirk helper ───────────────────────────────────────────────

def cwo_alias_for_request(user: str) -> str:
    """
    The server always prepends 'tmp' to whatever name you send. If the user
    already typed an alias starting with 'tmp' (e.g. --mail-id tmpfoo@chatcloud.site),
    strip it before sending so the round-trip address matches what they asked
    for. Otherwise send as-is and the caller is responsible for warning that
    the real address will differ.
    """
    if user.lower().startswith("tmp") and len(user) > 3:
        return user[3:]
    return user


# ── session management ───────────────────────────────────────────────────────

def _cwo_create(email_key: str, alias: str, cache: dict) -> dict:
    """POST /api/new_address, store result under email_key in cache + pool."""
    s = _cwo_pool.get(email_key, {}).get("session") or _cwo_new_session()
    body, status = _cwo_post(s, "/api/new_address", {"name": alias})
    if status != 200 or "jwt" not in body:
        raise RuntimeError(f"chatworkon: /api/new_address failed: {body}")

    jwt           = body["jwt"]
    real_address  = body.get("address", "")
    address_id    = _cwo_decode_jwt_address_id(jwt)

    _cwo_pool[email_key] = {"session": s, "jwt": jwt}
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["jwt"]        = jwt
    mb["address"]    = real_address
    mb["address_id"] = address_id
    save_cache(cache)

    if real_address and real_address != email_key:
        dbg(f"cwo: requested '{email_key}' but server assigned '{real_address}' (tmp-prefix quirk)")

    return mb


def _cwo_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Return a live (session, jwt) for email_key.

    1. In-process pool (already live this run).
    2. Restore jwt from cache, validate with a cheap GET /api/mails call.
    3. Mint a fresh address via /api/new_address.

    Returns (session, jwt).
    """
    if email_key in _cwo_pool:
        dbg(f"cwo: reusing live session for {email_key}")
        return _cwo_pool[email_key]["session"], _cwo_pool[email_key]["jwt"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_jwt = mb.get("jwt", "")

    s = _cwo_new_session()
    if saved_jwt:
        dbg(f"cwo: validating cached jwt for {email_key} ...")
        _, status = _cwo_get_authed(s, "/api/mails?limit=1&offset=0", saved_jwt)
        if status == 200:
            _cwo_pool[email_key] = {"session": s, "jwt": saved_jwt}
            return s, saved_jwt
        dbg(f"cwo: cached jwt for {email_key} no longer valid (HTTP {status}) - re-creating")

    user, _domain = email_key.split("@", 1)
    alias = cwo_alias_for_request(user)
    mb = _cwo_create(email_key, alias, cache)
    return _cwo_pool[email_key]["session"], _cwo_pool[email_key]["jwt"]


def cwo_list_mails(email_key: str, cache: dict, limit: int = 20, offset: int = 0) -> dict:
    """GET /api/mails for email_key. Returns the raw API body (results/count)."""
    s, jwt = _cwo_get_session(email_key, cache)
    body, status = _cwo_get_authed(s, f"/api/mails?limit={limit}&offset={offset}", jwt)
    if status != 200:
        return {"error": body.get("error", f"HTTP {status}")}
    return body


def cwo_get_settings(email_key: str, cache: dict) -> dict:
    """GET /api/settings for email_key (address + send_balance)."""
    s, jwt = _cwo_get_session(email_key, cache)
    body, status = _cwo_get_authed(s, "/api/settings", jwt)
    if status != 200:
        return {"error": body.get("error", f"HTTP {status}")}
    return body


def cwo_delete_local(email_key: str, cache: dict):
    """
    No server-side delete exists for this provider (confirmed live - the real
    web app only removes mailboxes from browser localStorage). This just drops
    the local cache entry and in-process session; nothing is called over the
    network.
    """
    _cwo_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)


# ── raw RFC822 parsing (no separate "fetch body" endpoint on this provider) ──

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


def cwo_parse_raw_email(raw: str) -> dict:
    """
    Parse a full RFC822 message (the `raw` field from /api/mails) into the
    same kind of dict shape cli_commands.py already expects from tempmailq's
    /get_messages + /msg/{id}: from/subject/date/content/attachments.
    """
    if not raw:
        return {"from": "unknown", "subject": "(no subject)", "date": "", "content": "", "attachments": []}

    msg = email_lib.message_from_string(raw, policy=policy.default)

    subject = _decode_header_value(msg.get("Subject", "")) or "(no subject)"
    from_name, from_email = parseaddr(msg.get("From", ""))
    from_name = _decode_header_value(from_name) or from_email or "unknown"
    date = msg.get("Date", "")

    text_body, html_body = "", ""
    attachments = []

    def _get_text(part):
        try:
            return part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            filename = part.get_filename()
            if "attachment" in disp or (filename and "inline" not in disp):
                payload = part.get_payload(decode=True) or b""
                attachments.append({
                    "filename": _decode_header_value(filename) if filename else "(unnamed)",
                    "content_type": ctype,
                    "size": len(payload),
                })
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

    return {
        "from":        from_name,
        "from_email":  from_email,
        "subject":     subject,
        "date":        date,
        "content":     text_body,
        "html_body":   html_body,
        "attachments": attachments,
    }
