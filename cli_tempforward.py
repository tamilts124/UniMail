#!/usr/bin/env python3
"""
cli_tempforward.py - tempforward.com client logic for the unimail.py CLI.

API PROTOCOL (tempforward.com) — internal REST JSON API.
  Captured via browser HAR 2026-07-19.

  base: https://tempforward.com/api/tempmail
  domain: tempforward.com (all addresses @tempforward.com)

  FLOW:
    1. POST /api/tempmail/create
       → {success: true, mailbox: {id, address, token, expires_at, created_at}}
       Token is an opaque hex string used for all subsequent requests.

    2. GET /api/tempmail/inbox?token=<token>
       → {mailbox: {id, address, expiresAt, timeLeftSeconds, createdAt}, emails: [...], count: N}
       emails[] items: {id, from, subject, date, preview, ...}

    3. GET /api/tempmail/email/<id>?token=<token>
       → full email with html/text body fields

    4. POST /api/tempmail/extend
       body: {token: "<token>"}
       → {success: true, mailbox: {id, address, token, expires_at}}

  AUTH: None required. Token passed as query param (stateless).
  Domain: tempforward.com (fixed)

SESSION MODEL:
  Cache entry (keyed by assigned address):
    {
      "tempforward_token": "<hex token>",
    }
"""

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

TEMPFORWARD_API  = "https://tempforward.com/api/tempmail"
TEMPFORWARD_SITE = "tempforward.com"


def _tempforward_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://tempforward.com/",
        "Origin":          "https://tempforward.com",
    })
    return s


def _tempforward_get(s: curl_requests.Session, path: str, token: str = "") -> tuple[dict, int]:
    url = TEMPFORWARD_API + path
    params = {"token": token} if token else {}
    dbg(f"tempforward: GET {url} params={params}")
    resp = s.get(url, params=params, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"tempforward: GET {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _tempforward_post(s: curl_requests.Session, path: str, data: dict = None) -> tuple[dict, int]:
    url = TEMPFORWARD_API + path
    dbg(f"tempforward: POST {url} data={data!r}")
    resp = s.post(url, json=data or {}, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"tempforward: POST {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _tempforward_save(email_key: str, token: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["tempforward_token"] = token
    save_cache(cache)


def tempforward_create_new(cache: dict) -> tuple[curl_requests.Session, str]:
    """
    POST /api/tempmail/create → assigned address + token.
    Returns (session, assigned_email_address).
    """
    s = _tempforward_session()
    body, status = _tempforward_post(s, "/create")
    if status != 200 or not body.get("success"):
        raise RuntimeError(f"tempforward: create failed (HTTP {status}): {body}")

    mailbox = body.get("mailbox", {})
    address = mailbox.get("address", "")
    token   = mailbox.get("token", "")
    if not address or not token:
        raise RuntimeError(f"tempforward: create response missing address/token: {body}")

    _tempforward_save(address, token, cache)
    dbg(f"tempforward: created inbox {address}")
    return s, address


def tempforward_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Restore session from cache (token-based, stateless).
    If token is missing, create a new account.
    Returns (session, token).
    """
    mb = cache.get("mailboxes", {}).get(email_key, {})
    token = mb.get("tempforward_token", "")

    s = _tempforward_session()

    if token:
        # Validate by pinging inbox
        body, status = _tempforward_get(s, f"/inbox", token)
        if status == 200 and body.get("mailbox"):
            dbg(f"tempforward: reusing cached token for {email_key}")
            return s, token
        dbg(f"tempforward: cached token invalid, creating new account")

    # No valid token — create new account
    _, new_address = tempforward_create_new(cache)
    new_mb = cache.get("mailboxes", {}).get(new_address, {})
    new_token = new_mb.get("tempforward_token", "")

    # If new address differs from email_key, add redirect
    if new_address != email_key:
        cache["mailboxes"].setdefault(email_key, {})["redirect_to"] = new_address
        save_cache(cache)

    return s, new_token


def tempforward_list_messages(email_key: str, cache: dict) -> list[dict]:
    """GET /api/tempmail/inbox?token=<token> → list of email summaries."""
    mb = cache.get("mailboxes", {}).get(email_key, {})
    token = mb.get("tempforward_token", "")
    if not token:
        raise RuntimeError(f"tempforward: no token cached for {email_key}")

    s = _tempforward_session()
    body, status = _tempforward_get(s, "/inbox", token)
    if status != 200:
        raise RuntimeError(f"tempforward: inbox failed (HTTP {status}): {body}")

    emails = body.get("emails", [])
    if isinstance(emails, list):
        return emails
    return []


def tempforward_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """GET /api/tempmail/email/<id>?token=<token> → full message."""
    mb = cache.get("mailboxes", {}).get(email_key, {})
    token = mb.get("tempforward_token", "")
    if not token:
        raise RuntimeError(f"tempforward: no token cached for {email_key}")

    s = _tempforward_session()
    body, status = _tempforward_get(s, f"/email/{msg_id}", token)
    if status != 200:
        raise RuntimeError(f"tempforward: get message {msg_id} failed (HTTP {status}): {body}")
    return body


def tempforward_delete_account(email_key: str, cache: dict):
    """Remove from local cache (no server-side delete endpoint observed)."""
    if email_key in cache.get("mailboxes", {}):
        del cache["mailboxes"][email_key]
        save_cache(cache)
    dbg(f"tempforward: removed {email_key} from cache")
