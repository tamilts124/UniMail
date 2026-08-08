#!/usr/bin/env python3
"""
cli_mailtm.py - mail.tm client logic for the unimail.py CLI.

API PROTOCOL (mail.tm) — public REST API, no API key required.
  docs: https://docs.mail.tm
  base: https://api.mail.tm

  All endpoints return JSON-LD (application/ld+json).

  FLOW:
    1. GET  /domains                 → find active domain(s)
    2. POST /accounts                → create account {address, password}
       → {id, address, ...}
    3. POST /token                   → get JWT  {address, password}
       → {token, id}
    4. GET  /messages                → list inbox (Bearer token)
       → {hydra:member: [{id, from, subject, intro, seen, createdAt, ...}]}
    5. GET  /messages/{id}           → full message (Bearer token)
       → {id, from, subject, text, html, ...}
    6. DELETE /messages/{id}         → delete message (Bearer token)
    7. DELETE /accounts/{id}         → delete account (Bearer token)

  AUTH: Bearer JWT in Authorization header.
  Rate limit: 8 QPS per IP.

SESSION MODEL:
  Each email address gets its own account on mail.tm's server.
  We store {account_id, password, token} in .unimail_cache.json.
  The token is re-fetched (POST /token) when it expires or is missing.
"""

import random
import string
import time

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

MAILTM_API = "https://api.mail.tm"

# in-process pool: email_key -> {"session": Session, "token": str, "account_id": str}
_mailtm_pool: dict[str, dict] = {}


def _mailtm_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json, application/ld+json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return s


def _mailtm_get(s: curl_requests.Session, path: str, token: str = "") -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    dbg(f"mailtm: GET {path}")
    resp = s.get(MAILTM_API + path, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"mailtm: GET {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _mailtm_post(s: curl_requests.Session, path: str, data: dict, token: str = "") -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    dbg(f"mailtm: POST {path} data={data!r}")
    resp = s.post(MAILTM_API + path, json=data, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"mailtm: POST {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _mailtm_delete(s: curl_requests.Session, path: str, token: str) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    dbg(f"mailtm: DELETE {path}")
    resp = s.delete(MAILTM_API + path, headers=headers, timeout=HTTP_TIMEOUT)
    dbg(f"mailtm: DELETE {path} -> {resp.status_code}")
    return resp.status_code


def mailtm_get_domains(s: curl_requests.Session) -> list[str]:
    """Return list of active domain names from /domains."""
    body, status = _mailtm_get(s, "/domains")
    if status != 200:
        return []
    members = body.get("hydra:member", [])
    return [m["domain"] for m in members if m.get("isActive") and not m.get("isPrivate")]


def _mailtm_get_token(s: curl_requests.Session, address: str, password: str) -> str:
    """POST /token to get a fresh JWT."""
    body, status = _mailtm_post(s, "/token", {"address": address, "password": password})
    if status == 200 and body.get("token"):
        return body["token"]
    raise RuntimeError(f"mail.tm: /token failed (HTTP {status}): {body}")


def _mailtm_save(email_key: str, s: curl_requests.Session,
                 token: str, account_id: str, password: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["mailtm_token"]      = token
    mb["mailtm_account_id"] = account_id
    mb["mailtm_password"]   = password
    save_cache(cache)


def mailtm_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str, str]:
    """
    Return (session, token, account_id) for email_key.
    1. In-process pool.
    2. Restore from cache — re-fetch token if needed.
    3. Create new account on mail.tm.
    """
    if email_key in _mailtm_pool:
        p = _mailtm_pool[email_key]
        dbg(f"mailtm: reusing live session for {email_key}")
        return p["session"], p["token"], p["account_id"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_token    = mb.get("mailtm_token", "")
    saved_id       = mb.get("mailtm_account_id", "")
    saved_password = mb.get("mailtm_password", "")

    s = _mailtm_new_session()

    # Try to restore from cache
    if saved_id and saved_password:
        dbg(f"mailtm: restoring session for {email_key} from cache ...")
        # Validate token by fetching /me
        if saved_token:
            _, status = _mailtm_get(s, "/me", saved_token)
            if status == 200:
                _mailtm_pool[email_key] = {"session": s, "token": saved_token, "account_id": saved_id}
                return s, saved_token, saved_id
            dbg(f"mailtm: cached token invalid (HTTP {status}), re-fetching ...")
        # Re-fetch token using saved password
        try:
            token = _mailtm_get_token(s, email_key, saved_password)
            _mailtm_pool[email_key] = {"session": s, "token": token, "account_id": saved_id}
            _mailtm_save(email_key, s, token, saved_id, saved_password, cache)
            return s, token, saved_id
        except Exception as e:
            dbg(f"mailtm: token re-fetch failed ({e}), creating new account")

    # Create new account -- fetch live domain in case seed has rotated
    live_domains = mailtm_get_domains(s)
    req_domain = email_key.split("@")[1] if "@" in email_key else ""
    user_part  = email_key.split("@")[0]
    if live_domains and req_domain not in live_domains:
        address = f"{user_part}@{live_domains[0]}"
        dbg(f"mailtm: domain '{req_domain}' not active, using live domain '{live_domains[0]}'")
    else:
        address = email_key
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    body, status = _mailtm_post(s, "/accounts", {"address": address, "password": password})
    if status not in (200, 201) or not body.get("id"):
        raise RuntimeError(f"mail.tm: /accounts creation failed (HTTP {status}): {body}")

    account_id = body["id"]
    real_addr  = address  # may differ from email_key if domain was remapped
    token = _mailtm_get_token(s, real_addr, password)

    _mailtm_pool[real_addr] = {"session": s, "token": token, "account_id": account_id}
    _mailtm_save(real_addr, s, token, account_id, password, cache)
    # also store a redirect in cache so the original key resolves
    if real_addr != email_key:
        mb2 = cache.setdefault("mailboxes", {}).setdefault(email_key, {})
        mb2["redirect_to"] = real_addr
        from cli_config import save_cache
        save_cache(cache)
    dbg(f"mailtm: created account {real_addr} (id={account_id})")
    return s, token, account_id


def mailtm_list_messages(email_key: str, cache: dict) -> list[dict]:
    """GET /messages — return list of message summaries."""
    s, token, _ = mailtm_get_session(email_key, cache)
    body, status = _mailtm_get(s, "/messages?page=1", token)
    if status != 200:
        raise RuntimeError(f"mail.tm: /messages failed (HTTP {status}): {body}")
    return body.get("hydra:member", [])


def mailtm_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """GET /messages/{id} — return full message with text/html body."""
    s, token, _ = mailtm_get_session(email_key, cache)
    body, status = _mailtm_get(s, f"/messages/{msg_id}", token)
    if status != 200:
        raise RuntimeError(f"mail.tm: /messages/{msg_id} failed (HTTP {status}): {body}")
    return body


def mailtm_delete_account(email_key: str, cache: dict):
    """DELETE /accounts/{id} — remove account from server and local cache."""
    mb = cache["mailboxes"].get(email_key, {})
    account_id = mb.get("mailtm_account_id", "")
    token = mb.get("mailtm_token", "")

    if account_id and token:
        s = _mailtm_pool.get(email_key, {}).get("session") or _mailtm_new_session()
        status = _mailtm_delete(s, f"/accounts/{account_id}", token)
        dbg(f"mailtm: DELETE /accounts/{account_id} -> {status}")

    _mailtm_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)
