#!/usr/bin/env python3
"""
cli_mailgw.py - mail.gw client logic for the unimail.py CLI.

API PROTOCOL (mail.gw) — identical to mail.tm, just different base URL.
  base: https://api.mail.gw
  docs: https://docs.mail.gw  (same spec as mail.tm)

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

  Domains observed (fetched live from /domains):
    oakon.com, teihu.com, raleigh-construction.com, pastryofistanbul.com, ...

SESSION MODEL:
  Each email address gets its own account on mail.gw's server.
  We store {account_id, password, token} in .unimail_cache.json under key
  "mailgw_*" so they don't collide with mail.tm entries.
"""

import random
import string
import time

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

MAILGW_API = "https://api.mail.gw"

# in-process pool: email_key -> {session, token, account_id}
_mailgw_pool: dict[str, dict] = {}


def _mailgw_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json, application/ld+json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return s


def _mailgw_get(s: curl_requests.Session, path: str, token: str = "") -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    dbg(f"mailgw: GET {path}")
    resp = s.get(MAILGW_API + path, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"mailgw: GET {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _mailgw_post(s: curl_requests.Session, path: str, data: dict, token: str = "") -> tuple[dict, int]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    dbg(f"mailgw: POST {path} data={data!r}")
    resp = s.post(MAILGW_API + path, json=data, headers=headers, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {}
    dbg(f"mailgw: POST {path} -> {resp.status_code}  body={str(body)[:200]}")
    return body, resp.status_code


def _mailgw_delete(s: curl_requests.Session, path: str, token: str) -> int:
    headers = {"Authorization": f"Bearer {token}"}
    dbg(f"mailgw: DELETE {path}")
    resp = s.delete(MAILGW_API + path, headers=headers, timeout=HTTP_TIMEOUT)
    dbg(f"mailgw: DELETE {path} -> {resp.status_code}")
    return resp.status_code


def mailgw_get_domains(s: curl_requests.Session) -> list[str]:
    """Return list of active domain names from /domains."""
    body, status = _mailgw_get(s, "/domains")
    if status != 200:
        return []
    members = body.get("hydra:member", [])
    return [m["domain"] for m in members if m.get("isActive") and not m.get("isPrivate")]


def _mailgw_get_token(s: curl_requests.Session, address: str, password: str) -> str:
    """POST /token to get a fresh JWT."""
    body, status = _mailgw_post(s, "/token", {"address": address, "password": password})
    if status == 200 and body.get("token"):
        return body["token"]
    raise RuntimeError(f"mail.gw: /token failed (HTTP {status}): {body}")


def _mailgw_save(email_key: str, s: curl_requests.Session,
                 token: str, account_id: str, password: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["mailgw_token"]      = token
    mb["mailgw_account_id"] = account_id
    mb["mailgw_password"]   = password
    save_cache(cache)


def mailgw_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str, str]:
    """
    Return (session, token, account_id) for email_key.
    1. In-process pool.
    2. Restore from cache — re-fetch token if needed.
    3. Create new account on mail.gw.
    """
    if email_key in _mailgw_pool:
        p = _mailgw_pool[email_key]
        dbg(f"mailgw: reusing live session for {email_key}")
        return p["session"], p["token"], p["account_id"]

    mb = cache["mailboxes"].get(email_key, {})
    saved_token    = mb.get("mailgw_token", "")
    saved_id       = mb.get("mailgw_account_id", "")
    saved_password = mb.get("mailgw_password", "")

    s = _mailgw_new_session()

    # Try to restore from cache
    if saved_id and saved_password:
        dbg(f"mailgw: restoring session for {email_key} from cache ...")
        if saved_token:
            _, status = _mailgw_get(s, "/me", saved_token)
            if status == 200:
                _mailgw_pool[email_key] = {"session": s, "token": saved_token, "account_id": saved_id}
                return s, saved_token, saved_id
            dbg(f"mailgw: cached token invalid (HTTP {status}), re-fetching ...")
        try:
            token = _mailgw_get_token(s, email_key, saved_password)
            _mailgw_pool[email_key] = {"session": s, "token": token, "account_id": saved_id}
            _mailgw_save(email_key, s, token, saved_id, saved_password, cache)
            return s, token, saved_id
        except Exception as e:
            dbg(f"mailgw: token re-fetch failed ({e}), creating new account")

    # Create new account — fetch live domain list
    live_domains = mailgw_get_domains(s)
    req_domain = email_key.split("@")[1] if "@" in email_key else ""
    user_part  = email_key.split("@")[0]
    if live_domains and req_domain not in live_domains:
        address = f"{user_part}@{live_domains[0]}"
        dbg(f"mailgw: domain '{req_domain}' not active, using live domain '{live_domains[0]}'")
    else:
        address = email_key
    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    body, status = _mailgw_post(s, "/accounts", {"address": address, "password": password})
    if status not in (200, 201) or not body.get("id"):
        raise RuntimeError(f"mail.gw: /accounts creation failed (HTTP {status}): {body}")

    account_id = body["id"]
    real_addr  = address
    token = _mailgw_get_token(s, real_addr, password)

    _mailgw_pool[real_addr] = {"session": s, "token": token, "account_id": account_id}
    _mailgw_save(real_addr, s, token, account_id, password, cache)
    if real_addr != email_key:
        mb2 = cache.setdefault("mailboxes", {}).setdefault(email_key, {})
        mb2["redirect_to"] = real_addr
        save_cache(cache)
    dbg(f"mailgw: created account {real_addr} (id={account_id})")
    return s, token, account_id


def mailgw_list_messages(email_key: str, cache: dict) -> list[dict]:
    """GET /messages — return list of message summaries."""
    s, token, _ = mailgw_get_session(email_key, cache)
    body, status = _mailgw_get(s, "/messages?page=1", token)
    if status != 200:
        raise RuntimeError(f"mail.gw: /messages failed (HTTP {status}): {body}")
    return body.get("hydra:member", [])


def mailgw_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """GET /messages/{id} — return full message with text/html body."""
    s, token, _ = mailgw_get_session(email_key, cache)
    body, status = _mailgw_get(s, f"/messages/{msg_id}", token)
    if status != 200:
        raise RuntimeError(f"mail.gw: /messages/{msg_id} failed (HTTP {status}): {body}")
    return body


def mailgw_delete_account(email_key: str, cache: dict):
    """DELETE /accounts/{id} — remove account from server and local cache."""
    mb = cache["mailboxes"].get(email_key, {})
    account_id = mb.get("mailgw_account_id", "")
    token = mb.get("mailgw_token", "")

    if account_id and token:
        s = _mailgw_pool.get(email_key, {}).get("session") or _mailgw_new_session()
        status = _mailgw_delete(s, f"/accounts/{account_id}", token)
        dbg(f"mailgw: DELETE /accounts/{account_id} -> {status}")

    _mailgw_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)
