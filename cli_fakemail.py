#!/usr/bin/env python3
"""
cli_fakemail.py - fakemail.net client logic for the unimail.py CLI.

API PROTOCOL (fakemail.net) — PHP session + AJAX endpoints.
  Captured via browser HAR 2026-07-19.

  base: https://www.fakemail.net
  domain observed: forliion.com (may rotate)

  FLOW:
    1. GET  /                         → set PHPSESSID cookie, HTML page with CSRF token
       Extract: const CSRF="..." from page HTML
       Cookie set: PHPSESSID=<session_id>, TMA=<url-encoded-email>
    2. GET  /index/index?csrf_token=CSRF  (X-Requested-With: XMLHttpRequest)
                                      → {email, heslo}
       Returns assigned email address and password.
    3. GET  /index/refresh            (X-Requested-With: XMLHttpRequest)
                                      → [] or [{id, od, predmet, predmetZkraceny, kdy, akce, precteno}]
       List messages; returns 0 (integer) when empty, or array.
    4. POST /index/email  body: id=<id>  (X-Requested-With: XMLHttpRequest)
                                      → {predmet, od, id, enc, telo}
       Get full message (telo = HTML body).
    5. POST /delete-email/<id>  body: id=<id>  (X-Requested-With: XMLHttpRequest)
                                      → 'ok'
    6. POST /index/new-email/  body: emailInput=<user>&format=json
                                      → redirect or JSON with new address
    7. POST /index/email-check/  body: email=<user>&format=json  → 'ok' or 'err'
       Check if username is available.

  AUTH:
    - PHPSESSID cookie (PHP session) identifies the server-side session.
    - TMA cookie stores current email address (URL-encoded).
    - CSRF token scraped from page HTML: const CSRF="..."
    - All AJAX endpoints require X-Requested-With: XMLHttpRequest header.

SESSION MODEL:
  Cache entry (keyed by email address):
    {
      "fakemail_csrf": "<token>",
    }
  PHPSESSID is stored in the curl_cffi session cookie jar.
"""

import re
import urllib.parse

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

FAKEMAIL_BASE  = "https://www.fakemail.net"
FAKEMAIL_SITE  = "fakemail.net"

_AJAX_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
}

# in-process pool: email_key -> {"session": Session, "csrf": str}
_fakemail_pool: dict[str, dict] = {}


def _fakemail_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         FAKEMAIL_BASE + "/",
        "Origin":          FAKEMAIL_BASE,
    })
    return s


def _scrape_csrf(html: str) -> str:
    """Extract CSRF token from page HTML: const CSRF="<token>" """
    m = re.search(r'const\s+CSRF\s*=\s*["\']([^"\']+)["\']', html)
    return m.group(1) if m else ""


def _scrape_email_from_tma(cookies) -> str:
    """Extract email from TMA cookie (URL-encoded)."""
    for cookie in cookies:
        if hasattr(cookie, 'name') and cookie.name == "TMA":
            return urllib.parse.unquote(cookie.value)
    return ""


def fakemail_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Return (session, csrf_token) for the given email address.
    Creates a new session on fakemail.net if not cached.
    """
    if email_key in _fakemail_pool:
        p = _fakemail_pool[email_key]
        return p["session"], p["csrf"]

    mb = cache.get("mailboxes", {}).get(email_key, {})
    saved_csrf = mb.get("fakemail_csrf", "")

    s = _fakemail_new_session()

    if saved_csrf:
        # Try to validate with a quick list call
        dbg(f"fakemail: validating cached session for {email_key}")
        try:
            # Set TMA cookie manually (server uses it to identify mailbox)
            s.cookies.set("TMA", urllib.parse.quote(email_key), domain="www.fakemail.net")
            resp = s.get(
                FAKEMAIL_BASE + "/index/refresh",
                headers=_AJAX_HEADERS,
                timeout=HTTP_TIMEOUT,
            )
            if resp.status_code == 200:
                dbg(f"fakemail: cached session valid for {email_key}")
                _fakemail_pool[email_key] = {"session": s, "csrf": saved_csrf}
                return s, saved_csrf
        except Exception as e:
            dbg(f"fakemail: cache validation failed: {e}")

    # Fresh session: GET homepage to get PHPSESSID + CSRF + TMA
    dbg(f"fakemail: creating new session, GET {FAKEMAIL_BASE}/")
    resp = s.get(FAKEMAIL_BASE + "/", timeout=HTTP_TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"fakemail: GET / failed (HTTP {resp.status_code})")

    csrf = _scrape_csrf(resp.text)
    if not csrf:
        raise RuntimeError("fakemail: could not find CSRF token in homepage HTML")
    dbg(f"fakemail: CSRF={csrf!r}")

    # Now call /index/index to get the assigned email
    resp2 = s.get(
        f"{FAKEMAIL_BASE}/index/index?csrf_token={csrf}",
        headers=_AJAX_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"fakemail: GET /index/index -> {resp2.status_code} body={resp2.text[:200]}")
    if resp2.status_code != 200:
        raise RuntimeError(f"fakemail: GET /index/index failed (HTTP {resp2.status_code})")

    # Strip UTF-8 BOM before JSON parse (server sends \xef\xbb\xbf prefix)
    import json as _json
    body = _json.loads(resp2.content.lstrip(b"\xef\xbb\xbf"))
    assigned_email = body.get("email", "")
    dbg(f"fakemail: assigned email={assigned_email!r}")

    # If user requested a specific username, try to set it
    user, domain = email_key.split("@", 1)
    if assigned_email and assigned_email.lower() != email_key.lower():
        dbg(f"fakemail: requesting specific address {email_key}")
        chg = s.post(
            FAKEMAIL_BASE + "/index/new-email/",
            data={"emailInput": user, "format": "json"},
            headers=_AJAX_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        dbg(f"fakemail: new-email -> {chg.status_code} body={chg.text[:200]}")
        # Re-scrape state
        resp3 = s.get(
            f"{FAKEMAIL_BASE}/index/index?csrf_token={csrf}",
            headers=_AJAX_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        if resp3.status_code == 200:
            import json as _json
            body3 = _json.loads(resp3.content.lstrip(b"\xef\xbb\xbf"))
            assigned_email = body3.get("email", assigned_email)
            dbg(f"fakemail: new assigned email={assigned_email!r}")

    # Cache
    real_key = assigned_email if assigned_email else email_key
    mb_entry = cache.setdefault("mailboxes", {}).setdefault(real_key, {})
    mb_entry["fakemail_csrf"] = csrf
    save_cache(cache)

    if real_key != email_key:
        cache["mailboxes"][email_key] = {"redirect_to": real_key}
        save_cache(cache)

    _fakemail_pool[real_key] = {"session": s, "csrf": csrf}
    return s, csrf


def fakemail_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /index/refresh  →  [] or [{id, od, predmet, predmetZkraceny, kdy, precteno}]
    Returns list of message dicts. Returns [] when inbox empty.
    """
    s, csrf = fakemail_get_session(email_key, cache)
    resp = s.get(
        FAKEMAIL_BASE + "/index/refresh",
        headers=_AJAX_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"fakemail: GET /index/refresh -> {resp.status_code}  body={resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(f"fakemail: /index/refresh failed (HTTP {resp.status_code})")
    # Strip UTF-8 BOM before JSON parse
    import json as _json
    result = _json.loads(resp.content.lstrip(b"\xef\xbb\xbf"))
    # Server returns 0 (int) when empty
    if result == 0 or result is None:
        return []
    if isinstance(result, list):
        return result
    return []


def fakemail_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """
    POST /index/email  body: id=<msg_id>
    Returns {predmet, od, id, enc, telo} where telo = HTML body.
    """
    s, csrf = fakemail_get_session(email_key, cache)
    resp = s.post(
        FAKEMAIL_BASE + "/index/email",
        data={"id": msg_id},
        headers=_AJAX_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"fakemail: POST /index/email id={msg_id} -> {resp.status_code}")
    if resp.status_code != 200:
        raise RuntimeError(f"fakemail: /index/email failed (HTTP {resp.status_code})")
    import json as _json
    return _json.loads(resp.content.lstrip(b"\xef\xbb\xbf"))


def fakemail_delete_message(email_key: str, msg_id: str, cache: dict):
    """POST /delete-email/<msg_id>  body: id=<msg_id>"""
    s, csrf = fakemail_get_session(email_key, cache)
    resp = s.post(
        f"{FAKEMAIL_BASE}/delete-email/{msg_id}",
        data={"id": msg_id},
        headers=_AJAX_HEADERS,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"fakemail: DELETE msg {msg_id} -> {resp.status_code} {resp.text[:100]}")


def fakemail_delete_account(email_key: str, cache: dict):
    """Remove local session. No server-side delete endpoint exists."""
    _fakemail_pool.pop(email_key, None)
    mbs = cache.get("mailboxes", {})
    if email_key in mbs:
        del mbs[email_key]
        save_cache(cache)
