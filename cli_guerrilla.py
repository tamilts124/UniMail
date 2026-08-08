#!/usr/bin/env python3
"""
cli_guerrilla.py - guerrillamail.com client logic for the unimail.py CLI.

API PROTOCOL (guerrillamail.com) — public stateless JSON API.
  base: https://api.guerrillamail.com/ajax.php
  docs: https://www.guerrillamail.com/GuerrillaMailAPI.html

  FLOW:
    1. GET  ?f=get_email_address [&lang=en&sid_token=<token>]
       → {email_addr, alias, alias_error, ts, sid_token, ref_mid, ...}
       Sets a sid_token (session). Optionally pass a desired alias.

    2. GET  ?f=set_email_user&email_user=<alias>&lang=en&sid_token=<token>
       → {email_addr, alias, sid_token, ...}
       Changes the email address username part. Domain is fixed.

    3. GET  ?f=get_email_list&offset=0&seq=0&sid_token=<token>
       → {list: [{mail_id, mail_from, mail_subject, mail_date, mail_read, mail_exerpt}], count, ...}

    4. GET  ?f=fetch_email&email_id=<mail_id>&sid_token=<token>
       → {mail_id, mail_from, mail_subject, mail_body, mail_date, ...}

    5. GET  ?f=del_email&email_ids[]=<id>&sid_token=<token>

  Available domains (as of 2026): grr.la, guerrillamailblock.com, sharklasers.com,
    guerrillamail.info, spam4.me, guerrillamail.biz, guerrillamail.de,
    guerrillamail.net, guerrillamail.org, guerrillamail.com, yopmail.fr

  AUTH: sid_token cookie/param (stateless session ID returned on first call).
  Note: Email address format is alias@domain. Only certain domains work.

SESSION MODEL:
  Each email_key gets its own sid_token stored in .unimail_cache.json.
  No account creation needed — just call get_email_address with desired alias.
"""

import time
from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

GUERRILLA_API = "https://api.guerrillamail.com/ajax.php"
GUERRILLA_BASE = "https://www.guerrillamail.com"

# Supported domains (checked 2026-07-19)
GUERRILLA_DOMAINS = [
    "guerrillamail.com",
    "guerrillamail.net",
    "guerrillamail.org",
    "guerrillamail.de",
    "guerrillamail.biz",
    "guerrillamail.info",
    "grr.la",
    "sharklasers.com",
    "spam4.me",
    "guerrillamailblock.com",
]

# in-process session pool: email_key -> {"session": Session, "sid_token": str}
_guerrilla_pool: dict[str, dict] = {}


def _guerrilla_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         GUERRILLA_BASE + "/",
    })
    return s


def _guerrilla_get(s: curl_requests.Session, params: dict) -> dict:
    dbg(f"guerrilla: GET {params}")
    resp = s.get(GUERRILLA_API, params=params, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    dbg(f"guerrilla: -> {resp.status_code} body={str(body)[:200]}")
    return body


def _guerrilla_save(email_key: str, sid_token: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["guerrilla_sid_token"] = sid_token
    save_cache(cache)


def guerrilla_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Return (session, sid_token) for email_key.
    1. In-process pool.
    2. Restore from cache — validate with get_email_list.
    3. Create new session via get_email_address + set_email_user.
    """
    if email_key in _guerrilla_pool:
        p = _guerrilla_pool[email_key]
        dbg(f"guerrilla: reusing live session for {email_key}")
        return p["session"], p["sid_token"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_token = mb.get("guerrilla_sid_token", "")
    user, domain = email_key.split("@", 1)

    s = _guerrilla_new_session()

    # Try restore from cache
    if saved_token:
        dbg(f"guerrilla: validating cached sid_token for {email_key}")
        body = _guerrilla_get(s, {"f": "get_email_list", "offset": 0, "seq": 0, "sid_token": saved_token})
        if "list" in body or body.get("count") is not None:
            _guerrilla_pool[email_key] = {"session": s, "sid_token": saved_token}
            return s, saved_token
        dbg(f"guerrilla: cached token expired, re-creating")

    # Get a new session
    body = _guerrilla_get(s, {"f": "get_email_address", "lang": "en"})
    sid_token = body.get("sid_token", "")
    if not sid_token:
        raise RuntimeError(f"guerrillamail: get_email_address failed: {body}")

    # Switch to desired email user
    body2 = _guerrilla_get(s, {"f": "set_email_user", "email_user": user, "lang": "en", "sid_token": sid_token})
    assigned_email = body2.get("email_addr", "")
    # Update token (may rotate)
    sid_token = body2.get("sid_token", sid_token)
    dbg(f"guerrilla: assigned email={assigned_email!r}")

    _guerrilla_pool[email_key] = {"session": s, "sid_token": sid_token}
    _guerrilla_save(email_key, sid_token, cache)
    return s, sid_token


def guerrilla_list_messages(email_key: str, cache: dict) -> list[dict]:
    """GET ?f=get_email_list — return list of message summaries."""
    s, sid_token = guerrilla_get_session(email_key, cache)
    body = _guerrilla_get(s, {"f": "get_email_list", "offset": 0, "seq": 0, "sid_token": sid_token})
    return body.get("list", [])


def guerrilla_get_message(email_key: str, mail_id: str, cache: dict) -> dict:
    """GET ?f=fetch_email — return full message with body."""
    s, sid_token = guerrilla_get_session(email_key, cache)
    body = _guerrilla_get(s, {"f": "fetch_email", "email_id": mail_id, "sid_token": sid_token})
    return body


def guerrilla_delete_account(email_key: str, cache: dict):
    """No server-side account deletion for guerrillamail — just clear local cache."""
    _guerrilla_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)
