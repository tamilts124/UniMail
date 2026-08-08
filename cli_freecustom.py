#!/usr/bin/env python3
"""
cli_freecustom.py - freecustom.email client logic for the unimail.py CLI.

API PROTOCOL (freecustom.email) — internal Next.js REST API, no public docs.
  Captured via browser JS source analysis 2026-07-19.

  base: https://www.freecustom.email/api

  FLOW:
    1. POST /api/auth                             → {token}  (no body needed)
       Returns a short-lived anonymous JWT (expires in 1 hour).
    2. GET  /api/domains                          → {success, data: [{domain, tier, ...}]}
       Headers: x-fce-client: web-client  (REQUIRED — 403 without it)
                Authorization: Bearer <token>
    3. GET  /api/public-mailbox?fullMailboxId=USER@DOMAIN
                                                  → {success, data: [...messages...]}
       Same headers. No account creation — any username on any domain works immediately.
       Messages list items: {id, from, to, subject, date, preview, ...}
    4. GET  /api/public-mailbox?fullMailboxId=USER@DOMAIN&messageId=MSG_ID
                                                  → {success, data: {id, from, to, subject,
                                                     html, text, date, attachments, ...}}
       Same headers. Fetches full message body.

  AUTH: Anonymous JWT in Authorization header + mandatory x-fce-client: web-client header.
  Token lifetime: 1 hour (3600s). No account creation / deletion needed.
  Stateless: any username@domain pair is a valid inbox with zero setup.

DOMAINS (as of 2026-07-19, fetched live from /api/domains):
  ditapi.info, ditcloud.info, ditdrive.info, ditgame.info, ditlearn.info,
  ditpay.info, ditplay.info, ditube.info, junkstopper.info, areueally.info,
  sqlcompiler.info, addmy.space, attachmy.site, nimbusreach.info, lumenbay.info,
  haloforge.online, haloforge.info, echoharbor.in

SESSION MODEL:
  Token is cached in .unimail_cache.json under key "freecustom_token" + "freecustom_token_exp".
  Re-fetched automatically when missing or within 60s of expiry.
"""

import time

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

FREECUSTOM_API  = "https://www.freecustom.email/api"
FREECUSTOM_SITE = "freecustom.email"

# Shared headers required for ALL API calls (401 / 403 without x-fce-client)
_FCE_HEADERS = {"x-fce-client": "web-client"}

# Global token cache: {"token": str, "exp": float}
_fce_token_cache: dict = {}

# in-process session pool (one shared session — stateless API, no per-inbox state)
_fce_session: curl_requests.Session | None = None


def _fce_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin":          "https://www.freecustom.email",
        "Referer":         "https://www.freecustom.email/",
        **_FCE_HEADERS,
    })
    return s


def _get_session() -> curl_requests.Session:
    global _fce_session
    if _fce_session is None:
        _fce_session = _fce_new_session()
    return _fce_session


def freecustom_get_token(cache: dict) -> str:
    """
    Return a valid anonymous JWT for freecustom.email.
    Uses in-memory cache first, then persistent cache, then fetches fresh.
    Token is re-fetched when within 60 s of expiry.
    """
    now = time.time()

    # 1. In-process cache
    if _fce_token_cache.get("token") and _fce_token_cache.get("exp", 0) - now > 60:
        dbg("freecustom: reusing in-process token")
        return _fce_token_cache["token"]

    # 2. Persistent cache
    saved_token = cache.get("freecustom_token", "")
    saved_exp   = cache.get("freecustom_token_exp", 0)
    if saved_token and saved_exp - now > 60:
        dbg("freecustom: restoring token from cache")
        _fce_token_cache["token"] = saved_token
        _fce_token_cache["exp"]   = saved_exp
        return saved_token

    # 3. Fetch fresh token
    dbg("freecustom: fetching new token via POST /api/auth")
    s = _get_session()
    resp = s.post(FREECUSTOM_API + "/auth", timeout=HTTP_TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"freecustom: POST /api/auth failed (HTTP {resp.status_code}): {resp.text[:200]}")
    body = resp.json()
    token = body.get("token", "")
    if not token:
        raise RuntimeError(f"freecustom: no token in /api/auth response: {body}")

    exp = now + 3540  # 59 min (token lasts 60 min, re-fetch 1 min early)
    _fce_token_cache["token"] = token
    _fce_token_cache["exp"]   = exp
    cache["freecustom_token"]     = token
    cache["freecustom_token_exp"] = exp
    save_cache(cache)
    dbg(f"freecustom: new token obtained (expires in ~59 min)")
    return token


def freecustom_get_domains(cache: dict) -> list[str]:
    """Fetch live domain list from /api/domains."""
    token = freecustom_get_token(cache)
    s = _get_session()
    resp = s.get(
        FREECUSTOM_API + "/domains",
        headers={"Authorization": f"Bearer {token}"},
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"freecustom: GET /api/domains -> {resp.status_code}")
    if resp.status_code != 200:
        raise RuntimeError(f"freecustom: /api/domains failed (HTTP {resp.status_code}): {resp.text[:200]}")
    body = resp.json()
    return [d["domain"] for d in body.get("data", [])]


def freecustom_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /api/public-mailbox?fullMailboxId=EMAIL
    Returns list of message summary dicts.
    """
    token = freecustom_get_token(cache)
    s = _get_session()
    url = f"{FREECUSTOM_API}/public-mailbox?fullMailboxId={email_key}"
    dbg(f"freecustom: GET {url}")
    resp = s.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=HTTP_TIMEOUT)
    dbg(f"freecustom: -> {resp.status_code}  body={resp.text[:200]}")
    if resp.status_code != 200:
        raise RuntimeError(f"freecustom: /api/public-mailbox failed (HTTP {resp.status_code}): {resp.text[:200]}")
    body = resp.json()
    if not body.get("success"):
        raise RuntimeError(f"freecustom: /api/public-mailbox returned success=false: {body}")
    return body.get("data", [])


def freecustom_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """
    GET /api/public-mailbox?fullMailboxId=EMAIL&messageId=MSG_ID
    Returns full message dict with html/text body.
    """
    token = freecustom_get_token(cache)
    s = _get_session()
    url = f"{FREECUSTOM_API}/public-mailbox?fullMailboxId={email_key}&messageId={msg_id}"
    dbg(f"freecustom: GET {url}")
    resp = s.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=HTTP_TIMEOUT)
    dbg(f"freecustom: -> {resp.status_code}  body={resp.text[:200]}")
    if resp.status_code != 200:
        raise RuntimeError(f"freecustom: get_message failed (HTTP {resp.status_code}): {resp.text[:200]}")
    body = resp.json()
    if not body.get("success"):
        raise RuntimeError(f"freecustom: get_message success=false: {body}")
    data = body.get("data")
    # data can be a list (single item) or a dict — normalise to dict
    if isinstance(data, list):
        return data[0] if data else {}
    return data or {}
