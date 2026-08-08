#!/usr/bin/env python3
"""
cli_10mm_net.py - 10minutemail.net client logic for the unimail.py CLI.

API PROTOCOL (10minutemail.net) — confirmed from probe 2026-07-21:
  Pure REST/JSON, stateless key-based (no cookies needed).
  The email address is server-assigned; the session is tracked by `key`.

  BASE URL: https://www.10minutemail.net

FLOW:
  1. GET /address.api.php
     → {mail_get_user, mail_get_mail, mail_get_host, mail_get_key, mail_left_time, ...}
     (Creates a new 10-minute session; returns unique key)

  2. GET /mail.api.php?requestType=getEmailList&secondsAgo=3600&key=<key>
     → null (empty) or array of message objects

  Each message: {mail_unique_id, mail_from, mail_subject, mail_date, mail_read, ...}

SESSION MODEL:
  email_key (server-assigned address) → {tenminnet_key, tenminnet_address} stored in cache.
  Key expires after 10 minutes (extendable). On expiry, create a new session.
"""

import time
import urllib.request
import json
import ssl

from cli_config import dbg, save_cache, HTTP_TIMEOUT

TENMINNET_BASE = "https://www.10minutemail.net"

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def _net_get(url: str) -> dict | list | None:
    """Simple GET returning parsed JSON or None."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Accept", "application/json, */*")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT, context=_ctx) as r:
        body = r.read()
        text = body.decode("utf-8", errors="replace")
        if text.strip() in ("null", ""):
            return None
        return json.loads(text)


def tenminnet_create_session(cache: dict) -> tuple[str, str]:
    """
    Create a new 10minutemail.net session.
    Returns (address, key).
    """
    dbg("10mm_net: GET /address.api.php to create new session")
    data = _net_get(TENMINNET_BASE + "/address.api.php")
    address = data.get("mail_get_mail", "")
    key = data.get("mail_get_key", "")
    if not address or not key:
        raise RuntimeError("10minutemail.net: could not get address/key")
    dbg(f"10mm_net: address={address!r} key={key!r}")

    mb = cache["mailboxes"].setdefault(address, {})
    mb["tenminnet_key"] = key
    mb["tenminnet_address"] = address
    mb["tenminnet_created_at"] = int(time.time())
    save_cache(cache)
    return address, key


def tenminnet_get_session(email_key: str, cache: dict) -> tuple[str, str]:
    """
    Return (address, key) for email_key. Creates new if not cached or expired.
    """
    mb = cache["mailboxes"].get(email_key, {})
    key = mb.get("tenminnet_key", "")
    address = mb.get("tenminnet_address", email_key)
    created_at = mb.get("tenminnet_created_at", 0)

    # Consider session expired after 9 min (key is valid 10 min but be safe)
    if key and (time.time() - created_at) < 540:
        dbg(f"10mm_net: reusing session for {email_key}, key={key!r}")
        return address, key

    dbg(f"10mm_net: session expired or missing for {email_key}, creating new")
    return tenminnet_create_session(cache)


def tenminnet_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /mail.api.php?requestType=getEmailList&secondsAgo=3600&key=<key>
    Returns list of message dicts (empty list if no mail).
    Each item: {mail_unique_id, mail_from, mail_subject, mail_date, mail_read, ...}
    """
    address, key = tenminnet_get_session(email_key, cache)
    url = TENMINNET_BASE + f"/mail.api.php?requestType=getEmailList&secondsAgo=3600&key={key}"
    dbg(f"10mm_net: GET /mail.api.php?requestType=getEmailList&key={key}")
    result = _net_get(url)
    if result is None:
        return []
    return result if isinstance(result, list) else []


def tenminnet_get_message(email_key: str, msg_id: str, cache: dict) -> dict | None:
    """
    GET /mail.api.php?requestType=getEmail&key=<key>&mailId=<msg_id>
    Returns full message dict or None.
    """
    address, key = tenminnet_get_session(email_key, cache)
    url = TENMINNET_BASE + f"/mail.api.php?requestType=getEmail&key={key}&mailId={msg_id}"
    dbg(f"10mm_net: GET single message mailId={msg_id}")
    try:
        return _net_get(url)
    except Exception as e:
        dbg(f"10mm_net: get_message error: {e}")
        return None


def tenminnet_delete_session(email_key: str, cache: dict):
    """Clear local session — no server-side delete endpoint."""
    cache["mailboxes"].pop(email_key, None)
    save_cache(cache)
    dbg(f"10mm_net: cleared local session for {email_key}")
