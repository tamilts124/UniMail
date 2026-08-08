#!/usr/bin/env python3
"""
cli_harakirimail.py - harakirimail.com client logic for the unimail.py CLI.

API PROTOCOL (harakirimail.com) — public REST API, fully stateless, no auth.
  Base: https://harakirimail.com
  Implemented: 2026-07-20 session-8.

  Completely stateless — any username@harakirimail.com is a valid inbox.
  Emails auto-deleted after 24h. No session, account creation, or auth needed.

  ENDPOINTS:
    GET /api/v1/inbox/<username>
      → {inbox, skip, limit, total_count, count, emails:[{_id, received,
             subject, from, spam}]}
      Lists messages (summary only, no body).

    GET /api/v1/email/<_id>
      → {_id, email:{original,original_host,host,user}, received,
             subject, from, to, bodytext, parts, inbox}
      Fetch full message by ID.

  DOMAIN: harakirimail.com (only one domain)
  SESSION MODEL: Fully stateless. No cache entry needed.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

HARAKIRIMAIL_BASE   = "https://harakirimail.com"
HARAKIRIMAIL_SITE   = "harakirimail.com"
HARAKIRIMAIL_DOMAIN = "harakirimail.com"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def harakirimail_list_messages(email: str) -> list[dict]:
    """
    GET /api/v1/inbox/<username>
    Returns list of message summary dicts.
    """
    username = email.split("@")[0]
    dbg(f"harakirimail: list_messages username={username!r}")
    r = requests.get(
        f"{HARAKIRIMAIL_BASE}/api/v1/inbox/{username}",
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"harakirimail: list_messages -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"harakirimail: list_messages failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    data = r.json()
    return data.get("emails", [])


def harakirimail_get_message(msg_id: str) -> dict:
    """
    GET /api/v1/email/<_id>
    Returns full message dict including bodytext.
    """
    dbg(f"harakirimail: get_message id={msg_id!r}")
    r = requests.get(
        f"{HARAKIRIMAIL_BASE}/api/v1/email/{msg_id}",
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"harakirimail: get_message -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"harakirimail: get_message failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    return r.json()
