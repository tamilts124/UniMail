#!/usr/bin/env python3
"""
cli_48hremail.py - 48hr.email client logic for the unimail.py CLI.

API PROTOCOL (48hr.email) — internal REST API, stateless, no auth.
  Base: https://48hr.email
  Implemented: 2026-07-21 session-21.

  The service is completely stateless — any username@48hr.email is a
  valid inbox. No session, account creation, or authentication required.
  Emails auto-delete after 48 hours.

  ENDPOINTS:
    GET /api/v1/inbox/<email>
      → {success, mode, data:[{uid, to, from, date, subject}], count, total}
      Lists all messages (header only). NOTE: email must be full address
      (user@48hr.email), not just username.

    GET /api/v1/inbox/<email>/<uid>
      → {success, mode, data:{uid, to, from, date, subject, text, html,
             attachments:[]}}
      Fetch a single message by UID (full body included).

    DELETE /api/v1/inbox/<email>/<uid>
      → Cloudflare-blocked (403); no delete supported via CLI.

  DOMAIN: 48hr.email (only one domain)
  SESSION MODEL: Fully stateless. No cache entry needed.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

HR48_BASE   = "https://48hr.email"
HR48_SITE   = "48hr.email"
HR48_DOMAIN = "48hr.email"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def hr48_list_messages(email: str) -> list[dict]:
    """
    GET /api/v1/inbox/<email>
    Returns list of message dicts (uid, to, from, date, subject).
    email must be the full address (user@48hr.email).
    """
    dbg(f"48hremail: list_messages email={email!r}")
    r = requests.get(
        f"{HR48_BASE}/api/v1/inbox/{email}",
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"48hremail: list_messages -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"48hremail: list_messages failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    data = r.json()
    return data.get("data", [])


def hr48_get_message(email: str, uid) -> dict:
    """
    GET /api/v1/inbox/<email>/<uid>
    Returns full message dict (includes text, html, attachments).
    """
    dbg(f"48hremail: get_message email={email!r} uid={uid!r}")
    r = requests.get(
        f"{HR48_BASE}/api/v1/inbox/{email}/{uid}",
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"48hremail: get_message -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"48hremail: get_message failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    return r.json().get("data", {})
