#!/usr/bin/env python3
"""
cli_10mm.py - 10minutemail.com client logic for the unimail.py CLI.

API PROTOCOL (10minutemail.com) — confirmed from HAR 2026-07-19:
  Pure REST/JSON with a PHP cookie session (JSESSIONID).
  Also uses Cloudflare (cf_clearance), but curl_cffi with chrome124 impersonation
  bypasses the JS challenge without interactive CAPTCHA.

  The email address and domain are ASSIGNED BY THE SERVER on first GET /.
  We cannot choose the address — only use what the server gives us.

  BASE URL: https://10minutemail.com

FLOW:
  1. GET /  → server sets JSESSIONID cookie + cf_clearance
  2. GET /session/address → {"address": "user@vtmpj.com"}  (the assigned address)
  3. GET /messages/messagesAfter/0 → array of message objects
     Each message: {id, sender, subject, sentDateFormatted, bodyPlainText, bodyHtmlContent}
  4. GET /session/reset → extend session by 10 more minutes

SESSION MODEL:
  Each assigned email_key maps to its own JSESSIONID in cache.
  If the session expires (address changes), a new one is created automatically.
"""

import time
from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT, TENMINMAIL_BASE

# in-process session pool: email_key -> {"session": Session, "address": str}
_10mm_pool: dict[str, dict] = {}


def _10mm_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         TENMINMAIL_BASE + "/",
    })
    return s


def _10mm_save(email_key: str, s: curl_requests.Session, address: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["10mm_session_cookies"] = dict(s.cookies)
    mb["10mm_address"]         = address
    save_cache(cache)


def _10mm_get_address(s: curl_requests.Session) -> str:
    """GET /session/address -> assigned email address string."""
    dbg("10mm: GET /session/address")
    resp = s.get(TENMINMAIL_BASE + "/session/address", timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
        return body.get("address", "")
    except Exception:
        return ""


def tenminmail_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Return (session, address) for email_key.

    10minutemail assigns addresses server-side. email_key is the address
    returned by the server on first call. We store JSESSIONID in cache and
    verify the session is still alive on restore.

    On first call, email_key should be the address the server gave us
    (stored during --mail-id). If the session expired, a new one is created
    and the NEW address is returned (caller should update cache accordingly).
    """
    if email_key in _10mm_pool:
        p = _10mm_pool[email_key]
        dbg(f"10mm: reusing live session for {email_key}")
        return p["session"], p["address"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_cookies = mb.get("10mm_session_cookies", {})

    s = _10mm_new_session()

    # Try restore from cache
    if saved_cookies:
        dbg(f"10mm: restoring session for {email_key} from cache")
        for k, v in saved_cookies.items():
            s.cookies.set(k, v, domain="10minutemail.com")
        address = _10mm_get_address(s)
        if address and address == email_key:
            dbg(f"10mm: session alive, address={address!r}")
            _10mm_pool[email_key] = {"session": s, "address": address}
            return s, address
        dbg(f"10mm: session expired or address mismatch ({address!r} vs {email_key!r}), creating new")

    # Fresh session — GET / first so server sets JSESSIONID
    dbg(f"10mm: creating new session via GET /")
    resp = s.get(TENMINMAIL_BASE + "/", timeout=HTTP_TIMEOUT)
    dbg(f"10mm: GET / -> {resp.status_code}")

    # Now get the assigned address
    address = _10mm_get_address(s)
    if not address:
        raise RuntimeError("10minutemail: could not obtain address from /session/address")

    dbg(f"10mm: assigned address={address!r}")
    _10mm_pool[address] = {"session": s, "address": address}
    _10mm_save(address, s, address, cache)
    return s, address


def tenminmail_create_new(cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Create a completely new 10minutemail session and return (session, address).
    Use this for --mail-id when the user wants a fresh 10minutemail address.
    """
    s = _10mm_new_session()
    dbg("10mm: GET / to init new session")
    resp = s.get(TENMINMAIL_BASE + "/", timeout=HTTP_TIMEOUT)
    dbg(f"10mm: GET / -> {resp.status_code}")
    address = _10mm_get_address(s)
    if not address:
        raise RuntimeError("10minutemail: could not obtain address from /session/address")
    dbg(f"10mm: new address={address!r}")
    _10mm_pool[address] = {"session": s, "address": address}
    _10mm_save(address, s, address, cache)
    return s, address


def tenminmail_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /messages/messagesAfter/0 — returns all messages as a list.
    Each item: {id, sender, subject, sentDateFormatted, bodyPlainText, bodyHtmlContent}
    """
    s, address = tenminmail_get_session(email_key, cache)
    dbg(f"10mm: GET /messages/messagesAfter/0")
    resp = s.get(TENMINMAIL_BASE + "/messages/messagesAfter/0", timeout=HTTP_TIMEOUT)
    dbg(f"10mm: -> {resp.status_code}  len={len(resp.text)}")
    try:
        return resp.json()
    except Exception as e:
        dbg(f"10mm: JSON parse error: {e}")
        return []


def tenminmail_reset_session(email_key: str, cache: dict):
    """GET /session/reset — extend mailbox expiry by 10 minutes."""
    s, address = tenminmail_get_session(email_key, cache)
    dbg("10mm: GET /session/reset")
    s.get(TENMINMAIL_BASE + "/session/reset", timeout=HTTP_TIMEOUT)


def tenminmail_delete_account(email_key: str, cache: dict):
    """No server-side account deletion for 10minutemail — just clear local cache."""
    _10mm_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)
