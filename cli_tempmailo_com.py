#!/usr/bin/env python3
"""
cli_tempmailo_com.py - tempmailo.com client logic for the unimail.py CLI.

NOTE: This module is for tempmailo.com (NOT to be confused with cli_tempmailio.py
      which handles temp-mail.io).

API PROTOCOL (tempmailo.com) - ASP.NET Core + Cloudflare protection.
  Updated 2026-07-19 session-4.

  base: https://tempmailo.com
  domains: denipl.net, denipl.com, fxzig.com

  KEY DISCOVERY (session-4):
    GET /changemail is rate-limited by Cloudflare (400 "Rate limit exceeded!")
    when called programmatically. However, POST / accepts ANY address at the
    known domains with no server-side ownership check. We generate the address
    locally (random username + known domain) and skip /changemail entirely.

  FLOW:
    1. Generate address locally: <random-8-chars>@<known-domain>
    2. GET / to get antiforgery token + cookies
    3. POST / with {"mail": "<address>"} to check inbox
       Returns JSON array of messages or [].

  AUTH:
    - ASP.NET antiforgery cookie set by curl_cffi on GET /
    - RequestVerificationToken header (scraped from HTML) required on POST /
    - No cf_clearance needed for GET / or POST / (only /changemail is rate-limited)

  SESSION MODEL:
    Cache: {"tempmailo_com_token": "<token>", "tempmailo_com_address": "<addr>"}
    Token refresh: GET / again if POST / returns 403.
"""

import re
import random
import string

from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

TEMPMAILO_COM_BASE    = "https://tempmailo.com"
TEMPMAILO_COM_SITE    = "tempmailo.com"
TEMPMAILO_COM_DOMAINS = ["denipl.net", "denipl.com", "fxzig.com"]

# In-process pool: email_key -> {"session": Session, "token": str}
_tempmailo_com_pool: dict[str, dict] = {}


def _tempmailo_com_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         TEMPMAILO_COM_BASE + "/",
        "Origin":          TEMPMAILO_COM_BASE,
    })
    return s


def _scrape_antiforgery_token(html: str) -> str:
    """Extract __RequestVerificationToken from hidden input in HTML."""
    m = re.search(
        r'<input[^>]+name=["\']__RequestVerificationToken["\'][^>]+value=["\']([^"\']+)["\']',
        html,
    )
    if m:
        return m.group(1)
    m = re.search(
        r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']__RequestVerificationToken["\']',
        html,
    )
    return m.group(1) if m else ""


def _generate_address() -> str:
    """Generate a random address at a known tempmailo.com domain."""
    length = random.randint(6, 10)
    user   = ''.join(random.choices(string.ascii_lowercase, k=length))
    domain = random.choice(TEMPMAILO_COM_DOMAINS)
    return f"{user}@{domain}"


def _fetch_token(s: curl_requests.Session) -> str:
    """GET / and scrape the antiforgery token. Raises on failure."""
    dbg(f"tempmailo_com: GET {TEMPMAILO_COM_BASE}/")
    resp = s.get(TEMPMAILO_COM_BASE + "/", timeout=HTTP_TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(
            f"tempmailo_com: GET / failed (HTTP {resp.status_code})"
        )
    token = _scrape_antiforgery_token(resp.text)
    if not token:
        raise RuntimeError(
            "tempmailo_com: could not find __RequestVerificationToken in homepage HTML"
        )
    dbg(f"tempmailo_com: token={token[:30]!r}...")
    return token


def _post_inbox(s, token: str, address: str):
    """POST / to list messages. Returns response object."""
    return s.post(
        TEMPMAILO_COM_BASE + "/",
        json={"mail": address},
        headers={
            "RequestVerificationToken": token,
            "Content-Type":             "application/json",
            "Accept":                   "application/json, text/plain, */*",
            "X-Requested-With":         "XMLHttpRequest",
        },
        timeout=HTTP_TIMEOUT,
    )


def tempmailo_com_create_new(cache: dict) -> tuple[curl_requests.Session, str]:
    """
    Create a new tempmailo.com mailbox:
      1. Generate random address locally (no /changemail  -  rate-limited)
      2. GET / to get antiforgery token
      3. Verify POST / works for the address
    Returns (session, address).
    """
    s       = _tempmailo_com_new_session()
    address = _generate_address()
    token   = _fetch_token(s)

    dbg(f"tempmailo_com: using generated address={address!r}")

    # Verify inbox endpoint works
    resp = _post_inbox(s, token, address)
    if resp.status_code == 403:
        dbg("tempmailo_com: POST / got 403, refreshing token...")
        token = _fetch_token(s)
        resp  = _post_inbox(s, token, address)

    if resp.status_code != 200:
        raise RuntimeError(
            f"tempmailo_com: POST / verification failed "
            f"(HTTP {resp.status_code}): {resp.text[:200]}"
        )
    dbg(f"tempmailo_com: address {address!r} verified OK")

    # Cache
    mb = cache.setdefault("mailboxes", {}).setdefault(address, {})
    mb["tempmailo_com_token"]   = token
    mb["tempmailo_com_address"] = address
    save_cache(cache)

    _tempmailo_com_pool[address] = {"session": s, "token": token}
    return s, address


def tempmailo_com_get_session(
    email_key: str, cache: dict
) -> tuple[curl_requests.Session, str]:
    """Return (session, token) for email_key. Restores pool -> cache -> new."""
    if email_key in _tempmailo_com_pool:
        p = _tempmailo_com_pool[email_key]
        return p["session"], p["token"]

    mb    = cache.get("mailboxes", {}).get(email_key, {})
    token = mb.get("tempmailo_com_token", "")

    if token:
        dbg(f"tempmailo_com: restoring cached session for {email_key}")
        s = _tempmailo_com_new_session()
        try:
            token = _fetch_token(s)   # always refresh  -  tokens are per-session
        except Exception as e:
            dbg(f"tempmailo_com: token refresh failed ({e}), using cached token")
        _tempmailo_com_pool[email_key] = {"session": s, "token": token}
        return s, token

    # Nothing cached  -  create fresh (address will differ from email_key)
    dbg(f"tempmailo_com: no cached entry for {email_key}, creating fresh")
    s, new_addr = tempmailo_com_create_new(cache)
    new_mb      = cache.get("mailboxes", {}).get(new_addr, {})
    new_token   = new_mb.get("tempmailo_com_token", "")
    if new_addr != email_key:
        cache["mailboxes"].setdefault(email_key, {})["redirect_to"] = new_addr
        save_cache(cache)
    return s, new_token


def tempmailo_com_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    POST / with {"mail": "<email>"}.
    Header: RequestVerificationToken: <token>
    Returns list of message dicts (text/html inline).
    """
    s, token = tempmailo_com_get_session(email_key, cache)

    resp = _post_inbox(s, token, email_key)
    dbg(f"tempmailo_com: POST / {email_key} -> {resp.status_code} {resp.text[:150]}")

    if resp.status_code == 403:
        dbg("tempmailo_com: 403 on POST /, refreshing token...")
        token = _fetch_token(s)
        _tempmailo_com_pool[email_key] = {"session": s, "token": token}
        mb = cache.get("mailboxes", {}).get(email_key, {})
        mb["tempmailo_com_token"] = token
        save_cache(cache)
        resp = _post_inbox(s, token, email_key)

    if resp.status_code != 200:
        raise RuntimeError(
            f"tempmailo_com: POST / failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    try:
        result = resp.json()
    except Exception:
        raise RuntimeError(
            f"tempmailo_com: POST / not JSON: {resp.text[:200]}"
        )

    return result if isinstance(result, list) else []


def tempmailo_com_delete_account(email_key: str, cache: dict):
    """Remove local state (no server-side delete endpoint)."""
    _tempmailo_com_pool.pop(email_key, None)
    mbs = cache.get("mailboxes", {})
    if email_key in mbs:
        del mbs[email_key]
        save_cache(cache)
    dbg(f"tempmailo_com: removed {email_key} from local cache")
