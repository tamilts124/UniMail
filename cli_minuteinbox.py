#!/usr/bin/env python3
"""
cli_minuteinbox.py - minuteinbox.com client logic for the unimail.py CLI.

API PROTOCOL (minuteinbox.com) — PHP session-based, cookie auth.
  Base: https://www.minuteinbox.com
  Implemented: 2026-07-21 session-15, fixed session-16.

  minuteinbox.com is a session-based disposable email service.
  A PHPSESSID cookie is issued on first visit; the inbox address is
  server-assigned via POST /index/index (XHR).

  ENDPOINTS:
    GET  /                          → sets PHPSESSID cookie
    POST /index/index               → {"email": "user@domain"} — assign inbox
    GET  /index/refresh             → [{id, predmet, predmetZkraceny, od, kdy, akce}, ...]
                                      Lists messages in current session's inbox.
    GET  /index/email?id=<id>       → HTML body of a single email
    POST /delete-email/             body: id=<id>  → "ok"
                                      Delete a single message.

  SESSION MODEL:
    Session is tied to PHPSESSID cookie.
    Cookies saved as dict to cache so session survives CLI restart.
    Address is server-assigned and stored in cache.

  DOMAIN: minafter.com (observed; may rotate — stored dynamically in cache)
  NOTE: Responses include a UTF-8 BOM — must decode with utf-8-sig.
"""

import json as _json
import requests

from cli_config import dbg, HTTP_TIMEOUT

MINUTEINBOX_BASE = "https://www.minuteinbox.com"
MINUTEINBOX_SITE = "minuteinbox.com"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.minuteinbox.com/",
}


def _decode(r) -> object:
    """Decode response handling UTF-8 BOM."""
    return _json.loads(r.content.decode("utf-8-sig"))



def minuteinbox_new_session() -> tuple[requests.Session, str]:
    """
    Full session bootstrap:
      1. GET /             → sets MI cookie (pre-session)
      2. POST /index/index → assigns email; expires MI cookie
      3. GET /index/refresh → establishes real PHPSESSID; returns [] (empty inbox)
    Returns (session, email_address).
    """
    s = requests.Session()
    s.headers.update(_HDR)

    dbg("minuteinbox: GET / (get MI pre-session cookie)")
    r = s.get(MINUTEINBOX_BASE + "/", timeout=HTTP_TIMEOUT)
    r.raise_for_status()

    dbg("minuteinbox: POST /index/index (assign inbox, expires MI)")
    r2 = s.post(MINUTEINBOX_BASE + "/index/index", timeout=HTTP_TIMEOUT)
    r2.raise_for_status()
    data = _decode(r2)
    email = data.get("email")
    if not email:
        raise RuntimeError(
            f"minuteinbox: POST /index/index returned no email: {r2.text[:200]}"
        )

    # Must call /index/refresh once to establish the real PHPSESSID cookie
    dbg("minuteinbox: GET /index/refresh (bootstrap PHPSESSID)")
    r3 = s.get(MINUTEINBOX_BASE + "/index/refresh", timeout=HTTP_TIMEOUT)
    # Status 500 is expected here on first call — PHPSESSID is now set in jar
    dbg(f"minuteinbox: refresh bootstrap status={r3.status_code} cookies={[c.name for c in s.cookies]!r}")

    dbg(f"minuteinbox: assigned email={email!r}")
    return s, email




def _cookies_to_dict(s: requests.Session) -> dict:
    """Extract all cookies from a requests.Session into a plain dict."""
    return {c.name: c.value for c in s.cookies}


def _save_session(cache: dict, email_key: str, s: requests.Session, real_addr: str):
    from cli_config import save_cache
    cookies = _cookies_to_dict(s)
    dbg(f"minuteinbox: saving cookies={cookies!r} addr={real_addr!r}")
    cache.setdefault("mailboxes", {}).setdefault(email_key, {}).update({
        "minuteinbox_cookies": cookies,
        "minuteinbox_address": real_addr,
    })
    save_cache(cache)


def minuteinbox_get_session(cache: dict, email_key: str) -> tuple[requests.Session, str]:
    """
    Restore session from cache or create a new one.
    Returns (session, real_email_address).
    """
    mb = cache.get("mailboxes", {}).get(email_key, {})
    cookies = mb.get("minuteinbox_cookies", {})
    real_addr = mb.get("minuteinbox_address", "")

    if cookies and real_addr:
        dbg(f"minuteinbox: restoring session for {email_key!r} cookies={list(cookies)!r}")
        s = requests.Session()
        s.headers.update(_HDR)
        for k, v in cookies.items():
            s.cookies.set(k, v, domain="www.minuteinbox.com", path="/")
        return s, real_addr

    # Create new session
    dbg(f"minuteinbox: creating new session (no cache for {email_key!r})")
    s, real_addr = minuteinbox_new_session()
    _save_session(cache, email_key, s, real_addr)
    return s, real_addr


def minuteinbox_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /index/refresh  →  list of message dicts.
    If session returns 500 (expired), create a new session and retry once.
    """
    s, real_addr = minuteinbox_get_session(cache, email_key)
    dbg(f"minuteinbox: list_messages for {real_addr!r}")
    r = s.get(MINUTEINBOX_BASE + "/index/refresh", timeout=HTTP_TIMEOUT)
    if r.status_code == 500:
        # Session expired — recreate
        dbg("minuteinbox: session expired (500), creating new session")
        # Clear cached session so get_session creates fresh
        cache.get("mailboxes", {}).get(email_key, {}).pop("minuteinbox_cookies", None)
        cache.get("mailboxes", {}).get(email_key, {}).pop("minuteinbox_address", None)
        s, real_addr = minuteinbox_get_session(cache, email_key)
        r = s.get(MINUTEINBOX_BASE + "/index/refresh", timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    msgs = _decode(r)
    dbg(f"minuteinbox: list_messages -> {len(msgs) if isinstance(msgs, list) else '?'} messages")
    return msgs if isinstance(msgs, list) else []


def minuteinbox_get_message(email_key: str, msg_id, cache: dict) -> str:
    """
    GET /index/email?id=<id>  →  HTML string of message body.
    """
    s, _ = minuteinbox_get_session(cache, email_key)
    dbg(f"minuteinbox: get_message id={msg_id!r}")
    r = s.get(
        MINUTEINBOX_BASE + "/index/email",
        params={"id": str(msg_id)},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.text


def minuteinbox_delete_message(email_key: str, msg_id, cache: dict) -> bool:
    """
    POST /delete-email/  body: id=<id>  →  "ok"
    """
    s, _ = minuteinbox_get_session(cache, email_key)
    dbg(f"minuteinbox: delete_message id={msg_id!r}")
    r = s.post(
        MINUTEINBOX_BASE + "/delete-email/",
        data={"id": str(msg_id)},
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"minuteinbox: delete_message -> {r.status_code} {r.text[:50]!r}")
    return r.status_code == 200 and r.text.strip().lower() == "ok"
