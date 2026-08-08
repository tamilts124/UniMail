#!/usr/bin/env python3
"""
cli_dropmail.py - dropmail.me client logic for the unimail.py CLI.

API PROTOCOL (dropmail.me) — GraphQL API, website token in URL path.

  base: https://dropmail.me/api/graphql/<token>

  TOKEN GENERATION:
    token = f"website_{random_part}_{fnv1a(random_part + secret)}"
    random_part = YYYYMMDD + 16 random alphanumeric chars
    secret = value of <meta name="csrf-token"> on the page (observed: "tm_graphql_secret_2026")
    fnv1a: custom FNV-1a 32-bit hash, returns lowercase hex

  FLOW:
    1. GET  https://dropmail.me/ → scrape <meta name="csrf-token"> for secret
    2. POST /api/graphql/<token>
         body: {"query": "mutation{introduceSession{id,expiresAt,addresses{address}}}"}
         → {data: {introduceSession: {id, expiresAt, addresses: [{address}]}}}
    3. POST /api/graphql/<token>
         body: {"query": "{session(id:\"<id>\"){addresses{address,mails{id,fromAddr,headerSubject,receivedAt,text,html}}}}"}
         → {data: {session: {addresses: [{address, mails: [...]}]}}}

  AUTH: Website token embedded in URL path (no Authorization header needed).

  DOMAINS (observed): spymail.one, pickmail.org, emlhub.com, emlpro.com, emltmp.com,
    freeml.net, mail2me.co, mailpwr.com, mailtowin.com, maximail.vip, mimimail.me,
    pickmemail.com, dropmail.me, 10mail.info, 10mail.org, 10mail.xyz, yomail.info

SESSION MODEL:
  Address is server-assigned on first call.
  We store {session_id, token, address} in .unimail_cache.json.
"""

import random
import string
import datetime

import requests

from cli_config import dbg, save_cache, HTTP_TIMEOUT

DROPMAIL_BASE   = "https://dropmail.me"
DROPMAIL_SECRET = "tm_graphql_secret_2026"   # from <meta name="csrf-token">

# in-process pool: email_key -> {session_id, token, address}
_dropmail_pool: dict[str, dict] = {}


# ── Token generation ─────────────────────────────────────────────────────────

def _fnv1a(s: str) -> str:
    """Custom FNV-1a 32-bit hash used by dropmail.me for token signing."""
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24)
        h &= 0xFFFFFFFF
    return format(h, 'x')


def _make_token(secret: str = DROPMAIL_SECRET) -> tuple[str, str]:
    """Return (token, random_part). random_part = date + 16 alphanum chars."""
    date_part   = datetime.date.today().strftime("%Y%m%d")
    rand_chars  = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    random_part = date_part + rand_chars
    token       = f"website_{random_part}_{_fnv1a(random_part + secret)}"
    return token, random_part


# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _gql(token: str, query: str) -> dict:
    url = f"{DROPMAIL_BASE}/api/graphql/{token}"
    dbg(f"dropmail: POST {url} query={query[:80]}")
    resp = requests.post(
        url,
        json={"query": query},
        headers={
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "Origin":       DROPMAIL_BASE,
            "Referer":      DROPMAIL_BASE + "/",
        },
        timeout=HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    body = resp.json()
    dbg(f"dropmail: response={str(body)[:200]}")
    if "errors" in body:
        raise RuntimeError(f"dropmail GraphQL error: {body['errors']}")
    return body.get("data", {})


# ── Public API ────────────────────────────────────────────────────────────────

def dropmail_create_session(cache: dict, email_key: str) -> str:
    """Create a new dropmail session. Returns the assigned email address."""
    token, _ = _make_token()
    data = _gql(token, "mutation{introduceSession{id,expiresAt,addresses{address}}}")
    sess = data.get("introduceSession", {})
    session_id = sess.get("id", "")
    addresses  = sess.get("addresses", [])
    address    = addresses[0]["address"] if addresses else ""
    if not session_id or not address:
        raise RuntimeError(f"dropmail: failed to create session: {data}")
    _dropmail_pool[email_key] = {"session_id": session_id, "token": token, "address": address}
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["dropmail_session_id"] = session_id
    mb["dropmail_token"]      = token
    mb["dropmail_address"]    = address
    # Remove any stale redirect_to that could cause chaining loops
    mb.pop("redirect_to", None)
    save_cache(cache)
    dbg(f"dropmail: created session id={session_id} address={address}")
    return address


def dropmail_get_session(cache: dict, email_key: str) -> tuple[str, str, str]:
    """Return (session_id, token, address), restoring from cache or creating new."""
    if email_key in _dropmail_pool:
        p = _dropmail_pool[email_key]
        return p["session_id"], p["token"], p["address"]
    mb = cache.get("mailboxes", {}).get(email_key, {})
    sid   = mb.get("dropmail_session_id", "")
    token = mb.get("dropmail_token", "")
    addr  = mb.get("dropmail_address", "")
    if sid and token and addr:
        _dropmail_pool[email_key] = {"session_id": sid, "token": token, "address": addr}
        return sid, token, addr
    # No cache — create fresh
    address = dropmail_create_session(cache, email_key)
    p = _dropmail_pool[email_key]
    return p["session_id"], p["token"], address


def dropmail_list_messages(email_key: str, cache: dict) -> list[dict]:
    """Return list of mail summaries for the session."""
    sid, token, _ = dropmail_get_session(cache, email_key)
    query = (
        '{session(id:"' + sid + '")'
        '{addresses{address,mails{id,fromAddr,headerSubject,receivedAt,text,html}}}}'
    )
    data    = _gql(token, query)
    session = data.get("session") or {}
    mails   = []
    for addr_obj in session.get("addresses", []):
        mails.extend(addr_obj.get("mails", []))
    return mails


def dropmail_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """Return full message dict (text/html already included in list query)."""
    msgs = dropmail_list_messages(email_key, cache)
    for m in msgs:
        if str(m.get("id", "")) == str(msg_id):
            return m
    raise RuntimeError(f"dropmail: message id={msg_id} not found")


def dropmail_delete_session(email_key: str, cache: dict):
    """Remove dropmail session from local cache (no server-side delete endpoint)."""
    _dropmail_pool.pop(email_key, None)
    if email_key in cache.get("mailboxes", {}):
        del cache["mailboxes"][email_key]
        save_cache(cache)
