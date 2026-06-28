#!/usr/bin/env python3
"""
cli_tmq.py - tempmailq.com client logic for the unimail.py CLI.

CSRF PROTOCOL (tempmailq.com) — confirmed from HAR 2026-06-27:
  Laravel uses TWO separate CSRF mechanisms simultaneously:

  1. x-xsrf-token HEADER  — the XSRF-TOKEN cookie value (base64 encrypted,
     set by server, rotates on every response). Axios reads it automatically
     from the cookie jar and sends it as this header.

  2. _token BODY FIELD — a plain 40-char alphanumeric token scraped from
     <meta name="csrf-token" content="..."> in the homepage HTML. This is
     the standard Laravel CSRF meta token. It is CONSTANT for the lifetime
     of the laravel_session cookie and is completely different from the
     XSRF-TOKEN cookie value.

  Both must be sent on every POST. Sending XSRF-TOKEN as _token (as the
  previous code did) causes 419 CSRF token mismatch on every request.

SESSION MODEL:
  Each email address owns its own independent curl_cffi Session with its
  own laravel_session + XSRF-TOKEN cookies + meta_token. Multiple mailboxes
  can be used simultaneously in the same process without interference.
  Per-mailbox state is persisted to .unimail_cache.json.
"""

import re, time, urllib.parse
from curl_cffi import requests as curl_requests

from cli_config import (
    dbg, save_cache, TEMPMAILQ_BASE, MAILDAX_BASE, DAKBOX_BASE, TEMPMAILWORLD_BASE,
    DISPOSABLE_BASE, IMPERSONATE, HTTP_TIMEOUT, parse_email,
)

# in-process session pool: email_key -> {"session": Session, "xsrf": str, "meta_token": str}
_tmq_pool: dict[str, dict] = {}


def _get_site_details(email_key: str) -> tuple[str, str]:
    user, domain, site = parse_email(email_key)
    if site == "maildax.cc":
        return MAILDAX_BASE, "maildax.cc"
    elif site == "dakbox.net":
        return DAKBOX_BASE, "dakbox.net"
    elif site == "temp-mail-world.com":
        return TEMPMAILWORLD_BASE, "temp-mail-world.com"
    elif site == "disposableemailgenerator.com":
        return DISPOSABLE_BASE, "disposableemailgenerator.com"
    else:
        return TEMPMAILQ_BASE, "tempmailq.com"


def _tmq_new_session(base_url: str) -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         base_url + "/",
        "Origin":          base_url,
    })
    return s


def _tmq_xsrf(s: curl_requests.Session) -> str:
    """Read decoded XSRF-TOKEN from the session cookie jar (for x-xsrf-token header)."""
    raw = s.cookies.get("XSRF-TOKEN")
    return urllib.parse.unquote(raw) if raw else ""


def _tmq_extract_meta_token(html_text: str) -> str:
    """
    Scrape the 40-char Laravel CSRF meta token from homepage HTML.
    Looks for: <meta name="csrf-token" content="TOKEN">
    """
    m = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([A-Za-z0-9+/=]{20,})["\']', html_text)
    if m:
        return m.group(1)
    # fallback: look for it in JS (window.Laravel.csrfToken or similar)
    m2 = re.search(r'["\']csrfToken["\']\s*:\s*["\']([A-Za-z0-9+/=]{20,})["\']', html_text)
    if m2:
        return m2.group(1)
    return ""


def _tmq_seed(s: curl_requests.Session, base_url: str) -> tuple[str, str]:
    """
    GET homepage. Returns (xsrf_cookie_value, meta_csrf_token).
    xsrf  -> sent as x-xsrf-token header on every POST
    meta  -> sent as _token body field on every POST
    """
    dbg(f"tmq: GET {base_url}/ ...")
    t0 = time.time()
    resp = s.get(base_url + "/", timeout=HTTP_TIMEOUT)
    xsrf = _tmq_xsrf(s)
    meta = _tmq_extract_meta_token(resp.text)
    dbg(f"tmq: GET / -> {resp.status_code} in {time.time()-t0:.2f}s  xsrf={xsrf[:20]!r}...  meta_token={meta!r}")
    return xsrf, meta


def _tmq_post(s: curl_requests.Session, base_url: str, endpoint: str, data: dict,
              xsrf: str, meta_token: str) -> tuple[dict, str, str]:
    """
    POST JSON:
      - body:   data + {"_token": meta_token}
      - header: x-xsrf-token: xsrf  (the XSRF-TOKEN cookie value, NOT meta_token)

    On 419: re-seeds and retries once.
    Returns (body, new_xsrf, meta_token).
    meta_token is returned unchanged (it's constant per session).
    """
    payload = dict(data)
    payload["_token"] = meta_token
    headers = {"x-xsrf-token": xsrf} if xsrf else {}
    dbg(f"tmq: POST {endpoint} _token={meta_token!r} x-xsrf={xsrf[:20]!r}... ...")
    t0 = time.time()
    resp = s.post(base_url + endpoint, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
    elapsed = time.time() - t0
    dbg(f"tmq: POST {endpoint} -> {resp.status_code} in {elapsed:.2f}s  body[:200]={resp.text[:200]!r}")

    if resp.status_code == 419:
        dbg("tmq: 419 — re-seeding and retrying once")
        xsrf, meta_token = _tmq_seed(s, base_url)
        payload["_token"] = meta_token
        headers = {"x-xsrf-token": xsrf} if xsrf else {}
        resp = s.post(base_url + endpoint, json=payload, headers=headers, timeout=HTTP_TIMEOUT)
        dbg(f"tmq: retry -> {resp.status_code}  body[:200]={resp.text[:200]!r}")

    # XSRF-TOKEN cookie may rotate on any response; keep it fresh
    xsrf = _tmq_xsrf(s) or xsrf

    try:
        body = resp.json()
    except Exception as e:
        dbg(f"tmq: JSON parse failed ({e})")
        body = {"error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

    return body, xsrf, meta_token


def _tmq_save(email_key: str, s: curl_requests.Session,
              xsrf: str, meta_token: str, email_token: str, cache: dict):
    """Persist session state to cache."""
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["session_cookies"] = dict(s.cookies)
    mb["xsrf_token"]      = xsrf
    mb["meta_token"]      = meta_token   # the constant _token from page HTML
    if email_token:
        mb["email_token"] = email_token
    save_cache(cache)


def _tmq_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str, str]:
    """
    Return a live (session, xsrf, meta_token) for email_key.

    Order of attempts:
    1. In-process pool (already live this run).
    2. Restore from cache cookies + tokens, validate with /get_messages.
       If alive but wrong address: /change to switch.
    3. Fresh GET / (seed) then /change to establish address.

    Returns (session, xsrf, meta_token).
    """
    # 1. Already live
    if email_key in _tmq_pool:
        p = _tmq_pool[email_key]
        xsrf = _tmq_xsrf(p["session"]) or p["xsrf"]
        dbg(f"tmq: reusing live session for {email_key}")
        return p["session"], xsrf, p["meta_token"]

    user, domain = email_key.split("@", 1)
    base_url, cookie_domain = _get_site_details(email_key)
    mb = cache["mailboxes"].get(email_key, {})

    # 2. Try restore from cache
    saved_cookies    = mb.get("session_cookies", {})
    saved_xsrf       = mb.get("xsrf_token", "")
    saved_meta_token = mb.get("meta_token", "")

    if saved_cookies and saved_xsrf and saved_meta_token:
        dbg(f"tmq: restoring session for {email_key} from cache ...")
        s = _tmq_new_session(base_url)
        for k, v in saved_cookies.items():
            s.cookies.set(k, v, domain=cookie_domain)
        body, xsrf, meta = _tmq_post(s, base_url, "/get_messages", {}, saved_xsrf, saved_meta_token)
        if "error" not in body:
            active = body.get("mailbox", "")
            dbg(f"tmq: /get_messages after restore -> active={active!r}")
            if active == email_key:
                _tmq_pool[email_key] = {"session": s, "xsrf": xsrf, "meta_token": meta}
                _tmq_save(email_key, s, xsrf, meta, body.get("email_token", ""), cache)
                return s, xsrf, meta
            # Session alive but on a different address — switch
            dbg(f"tmq: session on {active!r}, switching to {email_key!r}")
            body2, xsrf2, meta2 = _tmq_post(s, base_url, "/change", {"name": user, "domain": domain}, xsrf, meta)
            if "error" not in body2 and body2.get("mailbox") == email_key:
                _tmq_pool[email_key] = {"session": s, "xsrf": xsrf2, "meta_token": meta2}
                _tmq_save(email_key, s, xsrf2, meta2, body2.get("email_token", ""), cache)
                return s, xsrf2, meta2
        dbg(f"tmq: restore failed — fresh session for {email_key}")

    # 3. Fresh session
    s = _tmq_new_session(base_url)
    xsrf, meta = _tmq_seed(s, base_url)
    if not meta:
        raise RuntimeError(f"Laravel client: could not extract csrf meta token from homepage HTML ({base_url})")

    # The server only sets its mailbox/email cookie once /get_messages has been
    # called at least once on this session. Calling /change before that fails.
    body0, xsrf, meta = _tmq_post(s, base_url, "/get_messages", {}, xsrf, meta)
    if "error" in body0:
        raise RuntimeError(f"Laravel client: initial /get_messages failed: {body0}")
    dbg(f"tmq: initial /get_messages -> mailbox={body0.get('mailbox')!r}")

    body, xsrf, meta = _tmq_post(s, base_url, "/change", {"name": user, "domain": domain}, xsrf, meta)
    if "error" in body or not body.get("mailbox"):
        raise RuntimeError(f"Laravel client: /change failed: {body}")
    dbg(f"tmq: /change -> mailbox={body.get('mailbox')!r}")
    _tmq_pool[email_key] = {"session": s, "xsrf": xsrf, "meta_token": meta}
    _tmq_save(email_key, s, xsrf, meta, body.get("email_token", ""), cache)
    return s, xsrf, meta


def _tmq_call(email_key: str, endpoint: str, data: dict, cache: dict) -> dict:
    """Get session for email_key, POST endpoint, persist updated state, return body."""
    s, xsrf, meta = _tmq_get_session(email_key, cache)
    base_url, _ = _get_site_details(email_key)
    body, xsrf, meta = _tmq_post(s, base_url, endpoint, data, xsrf, meta)
    _tmq_pool[email_key] = {"session": s, "xsrf": xsrf, "meta_token": meta}
    _tmq_save(email_key, s, xsrf, meta, body.get("email_token", ""), cache)
    return body


def _tmq_fetch_message_html(email_key: str, msg_id: str, cache: dict) -> str:
    """
    GET /msg/{id} — returns the actual rendered email body HTML.
    """
    s, _, _ = _tmq_get_session(email_key, cache)
    base_url, _ = _get_site_details(email_key)
    url = f"{base_url}/msg/{msg_id}"
    headers = {
        "Accept":   "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer":  f"{base_url}/view/{msg_id}",
    }
    dbg(f"tmq: GET {url} ...")
    resp = s.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    dbg(f"tmq: GET /msg/{msg_id} -> {resp.status_code}  len={len(resp.text)}")
    if resp.status_code != 200:
        return ""
    return resp.text


def _tmq_get_message_body(email_key: str, msg_id: str, cache: dict) -> str:
    """
    GET /msg/{id} - the full message HTML body.
    """
    s, xsrf, meta = _tmq_get_session(email_key, cache)
    base_url, _ = _get_site_details(email_key)
    dbg(f"tmq: GET /msg/{msg_id} ...")
    resp = s.get(f"{base_url}/msg/{msg_id}", timeout=HTTP_TIMEOUT)
    dbg(f"tmq: GET /msg/{msg_id} -> {resp.status_code} ({len(resp.text)} bytes)")
    if resp.status_code != 200:
        return ""
    return resp.text
