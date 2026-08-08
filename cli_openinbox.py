#!/usr/bin/env python3
"""
cli_openinbox.py - openinbox.io client logic for the unimail.py CLI.

API PROTOCOL (openinbox.io) — re-confirmed from browser JS bundle 2026-07-19:
  REST JSON API at https://api.openinbox.io/api.
  No auth, no CSRF, no CAPTCHA for the free tier.

  The email address is ASSIGNED BY THE SERVER on POST /api/inbox.
  The returned {id} is an opaque UUID used for all subsequent calls.
  Free tier: 1 inbox, 1-hour expiry.

  BASE API URL: https://api.openinbox.io/api

FLOW:
  1. POST /api/inbox                        → {id, email, expiresAt, createdAt}
  2. GET  /api/inbox/{id}                   → {id, email, expiresAt, emailCount}
  3. GET  /api/emails/inbox/{id}            → {emails:[...], total, page, limit, hasMore}
     (NOTE: old path /api/inbox/{id}/emails returns 404 — changed 2026-07-19)
  4. GET  /api/emails/{email_id}            → full email with html body
  5. POST /api/emails/{email_id}/read       → mark as read
  6. DELETE /api/inbox/{id}                 → deletes inbox

  Domain as of 2026-07-19: inboxfly.space (old: inboxly.website)
  Both domains may be active; treat them interchangeably.

SESSION MODEL:
  The inbox id is persisted in .unimail_cache.json.
  Each email address maps to its inbox id.
  On restore, GET /api/inbox/{id} is used to validate the session (200 = alive).
"""

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

OPENINBOX_API  = "https://api.openinbox.io/api"
OPENINBOX_BASE = "https://openinbox.io"

# in-process session pool: email_key -> {"session": Session, "inbox_id": str}
_openinbox_pool: dict[str, dict] = {}


def _oi_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin":          OPENINBOX_BASE,
        "Referer":         OPENINBOX_BASE + "/",
        "Content-Type":    "application/json",
    })
    return s


def _oi_save(email_key: str, inbox_id: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["openinbox_id"]    = inbox_id
    mb["openinbox_email"] = email_key
    save_cache(cache)


def openinbox_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Return (session, inbox_id) for email_key.

    1. In-process pool.
    2. Restore from cache — validate with GET /api/inbox/{id} (200 = alive).
    3. Create new inbox via POST /api/inbox.
    """
    if email_key in _openinbox_pool:
        p = _openinbox_pool[email_key]
        dbg(f"openinbox: reusing live session for {email_key}")
        return p["session"], p["inbox_id"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_id = mb.get("openinbox_id", "")
    s = _oi_new_session()

    if saved_id:
        dbg(f"openinbox: validating cached inbox_id={saved_id!r} for {email_key}")
        # Use GET /api/inbox/{id} for validation (returns 200 while alive)
        resp = s.get(f"{OPENINBOX_API}/inbox/{saved_id}", timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            dbg(f"openinbox: session alive for {email_key}")
            _openinbox_pool[email_key] = {"session": s, "inbox_id": saved_id}
            return s, saved_id
        dbg(f"openinbox: cached id expired/invalid ({resp.status_code}), creating new inbox")

    s, inbox_id, _email = _openinbox_create_new(cache, s)
    return s, inbox_id


def openinbox_create_new(cache: dict) -> tuple[curl_requests.Session, str, str]:
    """
    Create a new openinbox.io inbox and return (session, inbox_id, assigned_email).
    """
    s = _oi_new_session()
    return _openinbox_create_new(cache, s)


def _openinbox_create_new(cache: dict, s: curl_requests.Session) -> tuple[curl_requests.Session, str, str]:
    dbg("openinbox: POST /api/inbox to create new inbox")
    resp = s.post(f"{OPENINBOX_API}/inbox", json={}, timeout=HTTP_TIMEOUT)
    dbg(f"openinbox: POST /api/inbox -> {resp.status_code}  body={resp.text[:200]!r}")
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"openinbox: POST /api/inbox failed: HTTP {resp.status_code}: {resp.text[:200]}")
    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"openinbox: JSON parse error: {e}")

    inbox_id = data.get("id", "")
    email    = data.get("email", "")
    if not inbox_id or not email:
        raise RuntimeError(f"openinbox: unexpected response: {data}")

    dbg(f"openinbox: created inbox_id={inbox_id!r} email={email!r}")
    _openinbox_pool[email] = {"session": s, "inbox_id": inbox_id}
    _oi_save(email, inbox_id, cache)
    return s, inbox_id, email


def openinbox_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /api/emails/inbox/{id} — returns paginated email list.
    Response: {emails:[{id, from, subject, receivedAt, bodyPreview, ...}], total, page, limit, hasMore}
    """
    s, inbox_id = openinbox_get_session(email_key, cache)
    dbg(f"openinbox: GET /api/emails/inbox/{inbox_id}")
    resp = s.get(
        f"{OPENINBOX_API}/emails/inbox/{inbox_id}",
        params={"page": 1, "limit": 30},
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"openinbox: -> {resp.status_code}  len={len(resp.text)}")
    if resp.status_code != 200:
        raise RuntimeError(f"openinbox: GET /emails/inbox failed: HTTP {resp.status_code}")
    try:
        data = resp.json()
        return data.get("emails", [])
    except Exception as e:
        dbg(f"openinbox: JSON parse error: {e}")
        return []


def openinbox_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """
    GET /api/emails/{email_id} — returns full message with html body.
    """
    s, _inbox_id = openinbox_get_session(email_key, cache)
    dbg(f"openinbox: GET /api/emails/{msg_id}")
    resp = s.get(f"{OPENINBOX_API}/emails/{msg_id}", timeout=HTTP_TIMEOUT)
    dbg(f"openinbox: -> {resp.status_code}  len={len(resp.text)}")
    if resp.status_code != 200:
        return {}
    try:
        return resp.json()
    except Exception:
        return {}


def openinbox_delete_inbox(email_key: str, cache: dict):
    """DELETE /api/inbox/{id} and clear from local cache."""
    mb = cache["mailboxes"].get(email_key, {})
    inbox_id = mb.get("openinbox_id", "")
    s = _openinbox_pool.get(email_key, {}).get("session") or _oi_new_session()

    if inbox_id:
        dbg(f"openinbox: DELETE /api/inbox/{inbox_id}")
        try:
            s.delete(f"{OPENINBOX_API}/inbox/{inbox_id}", timeout=HTTP_TIMEOUT)
        except Exception as e:
            dbg(f"openinbox: DELETE failed ({e}), continuing with local cleanup")

    _openinbox_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
    save_cache(cache)
