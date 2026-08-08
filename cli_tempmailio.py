#!/usr/bin/env python3
"""
cli_tempmailio.py - temp-mail.io client logic for the unimail.py CLI.

API PROTOCOL (temp-mail.io) — internal REST JSON API, no auth required.

  base: https://api.internal.temp-mail.io/api/v3
  Observed via browser HAR capture 2026-07-19.

  FLOW:
    1. Create new inbox (address assigned by server):
       POST https://api.internal.temp-mail.io/api/v3/email/new
       → { email: "user@domain.com", token: "...", ... }
       The 'email' field is the full assigned address.

    2. List messages:
       GET https://api.internal.temp-mail.io/api/v3/email/<address>/messages
       → [ { id, from, subject, body_text, body_html, created_at, ... }, ... ]
       Returns [] if empty. Polls on timer (~10s interval on the website).

    3. Get single message (no separate endpoint observed — full body included
       in list response; body_html / body_text included in each message object).

    4. Delete message (inferred from API pattern):
       DELETE https://api.internal.temp-mail.io/api/v3/email/<address>/messages/<id>
       → { status: "ok" }

  NOTES:
    - Address is server-assigned; user cannot choose.
    - Domain observed in testing: lnovic.com (may vary — multiple domains).
    - No session cookie or auth header required.
    - Messages typically include full body in the list response.
    - Inbox lifetime unknown; assume short-lived (< 24h).

SESSION MODEL:
  Cache entry:
    {
      "tempmailio_address": "user@domain.com",
    }
  Address stored in cache after creation. Stateless after that.
"""

from curl_cffi import requests as curl_requests

from cli_config import dbg, IMPERSONATE, HTTP_TIMEOUT

TEMPMAILIO_API = "https://api.internal.temp-mail.io/api/v3"
TEMPMAILIO_SITE = "temp-mail.io"


def _tempmailio_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://temp-mail.io/",
        "Origin":          "https://temp-mail.io",
    })
    return s


def tempmailio_create_new(cache: dict) -> tuple[curl_requests.Session, str]:
    """
    POST /email/new → assigned email address.
    Stores address in cache under a generated key.
    Returns (session, email_address).
    """
    s = _tempmailio_session()
    url = f"{TEMPMAILIO_API}/email/new"
    dbg(f"tempmailio: POST {url}")
    resp = s.post(url, json={}, timeout=HTTP_TIMEOUT)
    dbg(f"tempmailio: -> {resp.status_code}  body={resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"tempmailio: create failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    data = resp.json()
    address = data.get("email") or data.get("address")
    if not address:
        raise RuntimeError(
            f"tempmailio: create response missing email field: {resp.text[:200]}"
        )

    # Store in cache keyed by the assigned address itself
    cache.setdefault("mailboxes", {})[address] = {
        "tempmailio_address": address,
    }
    from cli_config import save_cache
    save_cache(cache)

    dbg(f"tempmailio: created inbox {address}")
    return s, address


def tempmailio_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Restore or validate an existing temp-mail.io session from cache.
    email_key is the assigned address (e.g. user@lnovic.com).
    Returns (session, address).
    """
    mb = cache.get("mailboxes", {}).get(email_key, {})
    address = mb.get("tempmailio_address", email_key)
    s = _tempmailio_session()
    # Validate by attempting to list messages
    url = f"{TEMPMAILIO_API}/email/{address}/messages"
    dbg(f"tempmailio: GET {url} (validate)")
    resp = s.get(url, timeout=HTTP_TIMEOUT)
    dbg(f"tempmailio: -> {resp.status_code}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"tempmailio: inbox check failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    return s, address


def tempmailio_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /email/<address>/messages → list of message dicts.
    Each message includes: id, from, subject, body_text, body_html, created_at.
    """
    mb = cache.get("mailboxes", {}).get(email_key, {})
    address = mb.get("tempmailio_address", email_key)
    s = _tempmailio_session()
    url = f"{TEMPMAILIO_API}/email/{address}/messages"
    dbg(f"tempmailio: GET {url}")
    resp = s.get(url, timeout=HTTP_TIMEOUT)
    dbg(f"tempmailio: -> {resp.status_code}  body={resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"tempmailio: list messages failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    data = resp.json()
    # API returns a list directly or wrapped; handle both
    if isinstance(data, list):
        return data
    return data.get("messages", data.get("data", []))


def tempmailio_delete_message(email_key: str, msg_id: str, cache: dict) -> bool:
    """
    DELETE /email/<address>/messages/<id>
    Returns True if deletion appears successful.
    """
    mb = cache.get("mailboxes", {}).get(email_key, {})
    address = mb.get("tempmailio_address", email_key)
    s = _tempmailio_session()
    url = f"{TEMPMAILIO_API}/email/{address}/messages/{msg_id}"
    dbg(f"tempmailio: DELETE {url}")
    try:
        resp = s.delete(url, timeout=HTTP_TIMEOUT)
        dbg(f"tempmailio: -> {resp.status_code}")
        return resp.status_code in (200, 204)
    except Exception:
        return False
