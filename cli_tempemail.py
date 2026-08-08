#!/usr/bin/env python3
"""
cli_tempemail.py - tempemail.cc client logic for the unimail.py CLI.

API PROTOCOL (tempemail.cc) — internal REST API, no public docs.
  Captured via browser HAR 2026-07-19.

  base: https://www.tempemail.cc/api
  domain: icmans.com (fetched live from /api/domains)

  FLOW:
    1. GET  /api/domains              → ["icmans.com", ...]
    2. POST /api/accounts             → {code, message, data: {id, email, password, token, ...}}
       Server assigns address (random username) if only domain given,
       or accepts full address. Token is returned directly in create response.
    3. POST /api/token                → {code, message, data: {token}}
       Used to refresh token when cached credentials are still valid.
    4. GET  /api/me                   → {code, message, data: {id, name, count, ...}}
       (Bearer token required)
    5. GET  /api/messages?limit=50    → {code, message, data: {items: [{id, from, subject, ...}], pagination: {...}}}
       (Bearer token required)
    6. GET  /api/messages/<id>        → {code, message, data: {id, from, subject, html, text, ...}}
       (Bearer token required)
    7. DELETE /api/messages/<id>      → {code, message} (Bearer token required)

  AUTH: Bearer JWT in Authorization header.
  Rate limits: ~10 account creations per IP per time window.

NOTES:
  - Address and password are both server-assigned on account creation.
  - Token expires; re-fetch via POST /api/token with stored credentials.
  - This API is structurally similar to mail.tm but uses a custom response
    envelope {code, message, data} and different endpoint paths.

SESSION MODEL:
  Cache entry (keyed by assigned email address):
    {
      "tempemail_token":      "eyJ...",
      "tempemail_account_id": "204719...",
      "tempemail_password":   "server-assigned-password",
    }
"""

import random
import string

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

TEMPEMAIL_API  = "https://www.tempemail.cc/api"
TEMPEMAIL_SITE = "tempemail.cc"

# in-process pool: email_key -> {"session": Session, "token": str, "account_id": str}
_tempemail_pool: dict[str, dict] = {}


def _tempemail_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://www.tempemail.cc/",
        "Origin":          "https://www.tempemail.cc",
    })
    return s


def _tempemail_get(s: curl_requests.Session, path: str, token: str = "") -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = TEMPEMAIL_API + path
    dbg(f"tempemail: GET {url}")
    resp = s.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"tempemail: GET {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _tempemail_post(s: curl_requests.Session, path: str, data: dict, token: str = "") -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = TEMPEMAIL_API + path
    dbg(f"tempemail: POST {url} data={data!r}")
    resp = s.post(url, json=data, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"tempemail: POST {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _tempemail_delete(s: curl_requests.Session, path: str, token: str) -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"}
    url = TEMPEMAIL_API + path
    dbg(f"tempemail: DELETE {url}")
    resp = s.delete(url, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"tempemail: DELETE {path} -> {resp.status_code}")
    return body, resp.status_code


def tempemail_get_domains(s: curl_requests.Session) -> list[str]:
    """Return list of active domain names from /api/domains."""
    body, status = _tempemail_get(s, "/domains")
    if status != 200:
        return []
    data = body.get("data", [])
    if isinstance(data, list):
        return [d for d in data if isinstance(d, str)]
    return []


def _tempemail_get_token(s: curl_requests.Session, address: str, password: str) -> str:
    """POST /api/token to get a fresh JWT."""
    body, status = _tempemail_post(s, "/token", {"email": address, "password": password})
    if status == 200 and body.get("code") == 200:
        token = (body.get("data") or {}).get("token", "")
        if token:
            return token
    raise RuntimeError(f"tempemail: /token failed (HTTP {status}): {body}")


def _tempemail_save(email_key: str, s: curl_requests.Session,
                    token: str, account_id: str, password: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["tempemail_token"]      = token
    mb["tempemail_account_id"] = account_id
    mb["tempemail_password"]   = password
    save_cache(cache)


def tempemail_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str, str]:
    """
    Return (session, token, account_id) for email_key.
    1. In-process pool.
    2. Restore from cache — re-fetch token if needed.
    3. Create new account on tempemail.cc.
    """
    if email_key in _tempemail_pool:
        p = _tempemail_pool[email_key]
        dbg(f"tempemail: reusing live session for {email_key}")
        return p["session"], p["token"], p["account_id"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_token    = mb.get("tempemail_token", "")
    saved_id       = mb.get("tempemail_account_id", "")
    saved_password = mb.get("tempemail_password", "")

    s = _tempemail_new_session()

    # Try to restore from cache
    if saved_id and saved_password:
        dbg(f"tempemail: restoring session for {email_key} from cache ...")
        if saved_token:
            me_body, me_status = _tempemail_get(s, "/me", saved_token)
            if me_status == 200 and me_body.get("code") == 200:
                _tempemail_pool[email_key] = {"session": s, "token": saved_token, "account_id": saved_id}
                return s, saved_token, saved_id
            dbg(f"tempemail: cached token invalid, re-fetching ...")
        try:
            token = _tempemail_get_token(s, email_key, saved_password)
            _tempemail_pool[email_key] = {"session": s, "token": token, "account_id": saved_id}
            _tempemail_save(email_key, s, token, saved_id, saved_password, cache)
            return s, token, saved_id
        except Exception as e:
            dbg(f"tempemail: token re-fetch failed ({e}), creating new account")

    # Create new account
    # Server assigns address if we POST with just the desired address.
    # Password is server-assigned and returned in the response.
    body, status = _tempemail_post(s, "/accounts", {"address": email_key})
    if status != 200 or body.get("code") != 200:
        raise RuntimeError(f"tempemail: /accounts creation failed (HTTP {status}): {body}")

    data = body.get("data", {})
    account_id = data.get("id", "")
    assigned_email = data.get("email", email_key)
    password = data.get("password", "")
    # Token is returned directly in the create response
    token = data.get("token", "")
    if not token:
        # Fallback: POST /api/token
        token = _tempemail_get_token(s, assigned_email, password)

    # Cache under the assigned address (may differ from requested if server changed it)
    cache_key = assigned_email
    _tempemail_pool[cache_key] = {"session": s, "token": token, "account_id": account_id}
    _tempemail_save(cache_key, s, token, account_id, password, cache)

    # If assigned_email != email_key, add a redirect so callers can find it
    if cache_key != email_key:
        cache["mailboxes"].setdefault(email_key, {})["redirect_to"] = cache_key
        save_cache(cache)

    dbg(f"tempemail: created account {assigned_email} (id={account_id})")
    return s, token, account_id


def tempemail_create_new(cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Create a fresh tempemail.cc inbox with a random username.
    Returns (session, assigned_email_address).
    """
    s = _tempemail_new_session()
    # Pick domain
    domains = tempemail_get_domains(s)
    domain = domains[0] if domains else "icmans.com"
    # Generate random username
    user = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{user}@{domain}"

    body, status = _tempemail_post(s, "/accounts", {"address": address})
    if status != 200 or body.get("code") != 200:
        # Try without specifying address (server picks one)
        body, status = _tempemail_post(s, "/accounts", {})
        if status != 200 or body.get("code") != 200:
            raise RuntimeError(f"tempemail: create failed (HTTP {status}): {body}")

    data = body.get("data", {})
    account_id    = data.get("id", "")
    assigned_email = data.get("email", address)
    password      = data.get("password", "")
    token         = data.get("token", "")
    if not token:
        token = _tempemail_get_token(s, assigned_email, password)

    _tempemail_pool[assigned_email] = {"session": s, "token": token, "account_id": account_id}
    _tempemail_save(assigned_email, s, token, account_id, password, cache)
    dbg(f"tempemail: created new inbox {assigned_email}")
    return s, assigned_email


def tempemail_list_messages(email_key: str, cache: dict) -> list[dict]:
    """GET /api/messages?limit=50 — return list of message summaries."""
    s, token, _ = tempemail_get_session(email_key, cache)
    body, status = _tempemail_get(s, "/messages?limit=50", token)
    if status != 200 or body.get("code") != 200:
        raise RuntimeError(f"tempemail: /messages failed (HTTP {status}): {body}")
    data = body.get("data", {})
    if isinstance(data, dict):
        return data.get("items", [])
    if isinstance(data, list):
        return data
    return []


def tempemail_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """GET /api/messages/<id> — return full message with html/text body."""
    s, token, _ = tempemail_get_session(email_key, cache)
    body, status = _tempemail_get(s, f"/messages/{msg_id}", token)
    if status != 200 or body.get("code") != 200:
        raise RuntimeError(f"tempemail: /messages/{msg_id} failed (HTTP {status}): {body}")
    return body.get("data", body)


def tempemail_delete_message(email_key: str, msg_id: str, cache: dict) -> bool:
    """DELETE /api/messages/<id> — delete a single message."""
    s, token, _ = tempemail_get_session(email_key, cache)
    body, status = _tempemail_delete(s, f"/messages/{msg_id}", token)
    dbg(f"tempemail: delete message {msg_id} -> HTTP {status}")
    return status == 200 and body.get("code") == 200


def tempemail_delete_account(email_key: str, cache: dict):
    """Remove account from local cache (no server-side account delete endpoint observed)."""
    _tempemail_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)
    dbg(f"tempemail: removed {email_key} from cache")
