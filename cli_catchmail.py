#!/usr/bin/env python3
"""
cli_catchmail.py - catchmail.io client logic for the unimail.py CLI.

API PROTOCOL (catchmail.io) — public REST API, fully stateless, no auth.
  Base: https://catchmail.io
  Implemented: 2026-07-20 session-5.

  The service is completely stateless — any username@catchmail.io is a
  valid inbox. No session, account creation, or authentication required.

  ENDPOINTS:
    GET /api/v1/mailbox?address=EMAIL
      → {address, page, page_size, messages:[{id, from, to, subject,
             body_text, body_html, received_at, attachments:[]}], count}
      Lists all messages (full body included). Returns empty list if none.

    GET /api/v1/message/{id}?mailbox=EMAIL
      → {id, from, to, subject, body_text, body_html, received_at, ...}
      Fetch a single message by ID.

    DELETE /api/v1/message/{id}
      → {} (204 or 200 on success)
      Delete a single message by ID.

  DOMAIN: catchmail.io (only one domain)
  SESSION MODEL: Fully stateless. No cache entry needed.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

CATCHMAIL_BASE   = "https://catchmail.io"
CATCHMAIL_SITE   = "catchmail.io"
CATCHMAIL_DOMAIN = "catchmail.io"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def catchmail_list_messages(email: str, page: int = 1) -> list[dict]:
    """
    GET /api/v1/mailbox?address=EMAIL
    Returns list of message dicts (full body included).
    """
    dbg(f"catchmail: list_messages email={email!r}")
    r = requests.get(
        f"{CATCHMAIL_BASE}/api/v1/mailbox",
        params={"address": email, "page": page},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"catchmail: list_messages -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"catchmail: list_messages failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    data = r.json()
    return data.get("messages", [])


def catchmail_get_message(msg_id: str, email: str) -> dict:
    """
    GET /api/v1/message/{id}?mailbox=EMAIL
    Returns full message dict.
    """
    dbg(f"catchmail: get_message id={msg_id!r} email={email!r}")
    r = requests.get(
        f"{CATCHMAIL_BASE}/api/v1/message/{msg_id}",
        params={"mailbox": email},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"catchmail: get_message -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"catchmail: get_message failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    return r.json()


def catchmail_delete_message(msg_id: str) -> bool:
    """
    DELETE /api/v1/message/{id}
    Returns True on success.
    """
    dbg(f"catchmail: delete_message id={msg_id!r}")
    r = requests.delete(
        f"{CATCHMAIL_BASE}/api/v1/message/{msg_id}",
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"catchmail: delete_message -> {r.status_code}")
    return r.status_code in (200, 204)
