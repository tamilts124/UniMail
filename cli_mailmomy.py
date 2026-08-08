#!/usr/bin/env python3
"""
cli_mailmomy.py - mailmomy.com client logic for the unimail.py CLI.

API PROTOCOL (mailmomy.com) — Public REST API, fully stateless, no auth.
  Base: https://mailmomy.com
  Implemented: 2026-07-19 session-4.

  The service is completely stateless — any username@<active_domain> is a
  valid inbox. No session, account creation, or authentication is required.
  Domains are discovered live from GET /api/domains.

  ENDPOINTS:
    GET /api/domains
      → [{domain, owner, email, addedAt, active, wildcard}, ...]
      Returns full list of domains; filter by active==true.

    GET /api/mail/messages?to=<email>&page=<n>&limit=<n>
      → {emails: [{id, recipient, from, subject, message, receivedAt}],
         total, page, limit, pages}
      Lists messages for any address. Returns empty list if none.

    GET /api/mail/messages?to=<email>&page=1&limit=1&id=<id>
      (No dedicated single-message endpoint found — full body is in the list)
      The 'message' field in each list item contains the full HTML body.

    DELETE /api/mail/delete?to=<email>
      → {deleted: N}
      Delete all messages for an address.

    DELETE /api/mail/delete?id=<message_id>
      → {deleted: N}
      Delete a single message by ID.

  SESSION MODEL:
    Fully stateless. No cache entry needed beyond the address itself.
    Domains fetched live; fallback list below for offline use.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

MAILMOMY_BASE = "https://mailmomy.com"
MAILMOMY_SITE = "mailmomy.com"

# Seed list — fetched live from /api/domains at runtime
MAILMOMY_DOMAINS_SEED = [
    "mailmomy.com",
    "2famail.com",
    "xikemail.com",
    "protect.support",
    "easyme.pro",
    "282mail.com",
]

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def mailmomy_get_domains() -> list[str]:
    """Fetch the current list of active domains from /api/domains."""
    try:
        r = requests.get(
            f"{MAILMOMY_BASE}/api/domains",
            headers=_HDR,
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                active = [d["domain"] for d in data if d.get("active")]
                if active:
                    dbg(f"mailmomy: got {len(active)} active domains")
                    return active
    except Exception as e:
        dbg(f"mailmomy: get_domains failed: {e}")
    return MAILMOMY_DOMAINS_SEED


def mailmomy_list_messages(email: str, page: int = 1, limit: int = 50) -> list[dict]:
    """
    GET /api/mail/messages?to=<email>&page=<n>&limit=<n>
    Returns list of message dicts with full body in 'message' field.
    """
    dbg(f"mailmomy: list_messages email={email!r}")
    r = requests.get(
        f"{MAILMOMY_BASE}/api/mail/messages",
        params={"to": email, "page": page, "limit": limit},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"mailmomy: list_messages -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"mailmomy: list_messages failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    data = r.json()
    return data.get("emails", [])


def mailmomy_delete_all(email: str) -> int:
    """
    DELETE /api/mail/delete?to=<email>
    Returns number of deleted messages.
    """
    dbg(f"mailmomy: delete_all email={email!r}")
    r = requests.delete(
        f"{MAILMOMY_BASE}/api/mail/delete",
        params={"to": email},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"mailmomy: delete_all -> {r.status_code} {r.text[:150]}")
    if r.status_code != 200:
        return 0
    return r.json().get("deleted", 0)


def mailmomy_delete_message(msg_id: str) -> bool:
    """
    DELETE /api/mail/delete?id=<msg_id>
    Returns True if at least one message was deleted.
    """
    dbg(f"mailmomy: delete_message id={msg_id!r}")
    r = requests.delete(
        f"{MAILMOMY_BASE}/api/mail/delete",
        params={"id": msg_id},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"mailmomy: delete_message -> {r.status_code} {r.text[:100]}")
    if r.status_code != 200:
        return False
    return r.json().get("deleted", 0) > 0
