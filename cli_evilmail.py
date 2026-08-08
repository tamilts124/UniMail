#!/usr/bin/env python3
"""
cli_evilmail.py - evilmail.pro client logic for the unimail.py CLI.

API PROTOCOL (evilmail.pro) — REST API, session-based, no auth key needed.
  Base: https://evilmail.pro
  Implemented: 2026-07-21 session-22.

  The service creates a disposable inbox by POSTing to /api/temp-email.
  A sessionToken is returned which is used to poll for messages.
  No API key is required for the create + poll flow.

  ENDPOINTS:
    POST /api/temp-email
      Body: {"domain": "evilbx.com", "ttlMinutes": 60}
      → {status:"success", data:{email, domain, sessionToken, ttlMinutes, expiresAt}}
      Creates a new disposable inbox.

    GET /api/temp-email/<sessionToken>
      → {status:"success", data:{email, domain, expiresAt, messages:[
            {uid, from, subject, body?, receivedAt}]}}
      Lists messages for the session. Returns empty messages list if none.

  DOMAIN: evilbx.com (free tier domain; domain list requires API key)
  SESSION MODEL: Token-based. sessionToken stored in cache under email key.
  NOTE: No per-message delete endpoint available without API key.
        Emails auto-expire when the TTL runs out.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

EVILMAIL_BASE   = "https://evilmail.pro"
EVILMAIL_SITE   = "evilmail.pro"
EVILMAIL_DOMAIN = "evilbx.com"
EVILMAIL_TTL    = 60  # minutes

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}


def evilmail_create_inbox(domain: str = EVILMAIL_DOMAIN, ttl: int = EVILMAIL_TTL) -> dict:
    """
    POST /api/temp-email
    Returns dict with keys: email, sessionToken, expiresAt
    """
    dbg(f"evilmail: create_inbox domain={domain!r} ttl={ttl}")
    r = requests.post(
        f"{EVILMAIL_BASE}/api/temp-email",
        json={"domain": domain, "ttlMinutes": ttl},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"evilmail: create_inbox -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"evilmail: create_inbox failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    resp = r.json()
    if resp.get("status") != "success":
        raise RuntimeError(f"evilmail: create_inbox error: {resp}")
    return resp["data"]


def evilmail_list_messages(session_token: str) -> tuple[list[dict], str]:
    """
    GET /api/temp-email/<sessionToken>
    Returns (messages_list, email_address).
    messages items have keys: uid, from, subject, body, receivedAt
    """
    dbg(f"evilmail: list_messages token={session_token[:16]}...")
    r = requests.get(
        f"{EVILMAIL_BASE}/api/temp-email/{session_token}",
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"evilmail: list_messages -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"evilmail: list_messages failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    resp = r.json()
    if resp.get("status") != "success":
        raise RuntimeError(f"evilmail: list_messages error: {resp}")
    data = resp["data"]
    return data.get("messages", []), data.get("email", "")
