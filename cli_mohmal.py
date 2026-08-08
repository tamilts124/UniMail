#!/usr/bin/env python3
"""
cli_mohmal.py - mohmal.com client logic for the unimail.py CLI.

API PROTOCOL (mohmal.com) — server-side HTML, cookie-based session (HttpOnly).
  Captured via browser 2026-07-20.

  base: https://www.mohmal.com
  domain observed: emailinbo.live (may rotate)

  FLOW:
    1. GET  /en/create/random             → creates server session; redirects to /en/inbox
       Sets HttpOnly session cookie (not JS-readable from browser, but readable via requests).
    2. GET  /en/inbox                     → HTML page with:
         - <div class="email">USER@DOMAIN</div>  — assigned email address
         - <table id="inbox-table"> with rows:
             <tr data-msg-id="ID" class="unseen|seen">
               <td class="subject"><a href="#">SUBJECT</a></td>
               <td class="time"><a href="#">TIME</a></td>
               <td class="sender"><a href="#">FROM</a></td>
             </tr>
    3. GET  /en/refresh                   → same HTML format as /en/inbox (poll for new mail)
    4. GET  /en/message/<id>              → plain HTML body of the message
    5. GET  /en/logout                    → deletes session and clears inbox (no per-message delete)

  AUTH:
    - Session maintained via HttpOnly cookie set by server.
    - curl_cffi Session stores cookies automatically.
    - Cookies are serialized to cache to survive process restarts.
"""

import re
import html as _html_module

from curl_cffi import requests as curl_requests

from cli_config import dbg, HTTP_TIMEOUT, IMPERSONATE, save_cache

MOHMAL_BASE = "https://www.mohmal.com"
MOHMAL_SITE = "mohmal.com"

# in-process pool: email_key -> {"session": Session}
_mohmal_pool: dict[str, dict] = {}


def _mohmal_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         MOHMAL_BASE + "/en",
    })
    return s


def _scrape_email(html: str) -> str:
    """Extract email from <div class="email">USER@DOMAIN</div>."""
    m = re.search(r'<div\s+class=["\']email["\'][^>]*>\s*([\w.+-]+@[\w.-]+\.[a-z]{2,})\s*</div>', html, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Fallback: any email-like pattern near the word "email"
    m2 = re.search(r'([\w.+-]+@[\w.-]+\.[a-z]{2,})', html)
    return m2.group(1).strip() if m2 else ""


def _scrape_messages(html: str) -> list[dict]:
    """
    Extract message list from #inbox-table HTML.
    Returns list of dicts: {id, subject, sender, time}.
    """
    msgs = []
    # Find all rows with data-msg-id
    for m in re.finditer(
        r'<tr\s+data-msg-id=["\'](\d+)["\'][^>]*>([\s\S]*?)</tr>',
        html, re.IGNORECASE
    ):
        msg_id = m.group(1)
        row_html = m.group(2)

        subject_m = re.search(r'class=["\']subject["\'][^>]*>.*?<a[^>]*>([\s\S]*?)</a>', row_html, re.IGNORECASE)
        time_m    = re.search(r'class=["\']time["\'][^>]*>.*?<a[^>]*>([\s\S]*?)</a>', row_html, re.IGNORECASE)
        sender_m  = re.search(r'class=["\']sender["\'][^>]*>.*?<a[^>]*>([\s\S]*?)</a>', row_html, re.IGNORECASE)

        def clean(s):
            if not s: return ""
            s = re.sub(r'<[^>]+>', '', s)
            return _html_module.unescape(s.strip())

        msgs.append({
            "id":      msg_id,
            "subject": clean(subject_m.group(1)) if subject_m else "",
            "time":    clean(time_m.group(1))    if time_m    else "",
            "sender":  clean(sender_m.group(1))  if sender_m  else "",
        })
    return msgs


def _cookies_to_dict(session: curl_requests.Session) -> dict:
    """Serialize session cookies to a plain dict for cache storage."""
    try:
        return dict(session.cookies)
    except Exception:
        return {}


def _restore_session(cookies: dict) -> curl_requests.Session:
    """Restore a session from serialized cookies."""
    s = _mohmal_new_session()
    for name, value in cookies.items():
        s.cookies.set(name, value, domain="www.mohmal.com")
    return s


def mohmal_create_session() -> tuple:
    """
    Create a new mohmal session and return (session, email).
    GETs /en/create/random which redirects to /en/inbox with assigned email.
    """
    s = _mohmal_new_session()
    dbg(f"mohmal: GET {MOHMAL_BASE}/en/create/random")
    resp = s.get(
        MOHMAL_BASE + "/en/create/random",
        timeout=HTTP_TIMEOUT,
        allow_redirects=True,
    )
    dbg(f"mohmal: create/random -> {resp.status_code} final_url={resp.url}")
    if resp.status_code != 200:
        raise RuntimeError(f"mohmal: /en/create/random failed (HTTP {resp.status_code})")

    email = _scrape_email(resp.text)
    if not email:
        raise RuntimeError("mohmal: could not find email in /en/inbox HTML")

    dbg(f"mohmal: assigned email={email!r}")
    _mohmal_pool[email] = {"session": s}
    return s, email


def mohmal_get_session(email_key: str, cache: dict) -> curl_requests.Session:
    """
    Return a session for the given email.
    Tries in-process pool first, then restores from cached cookies.
    """
    if email_key in _mohmal_pool:
        return _mohmal_pool[email_key]["session"]

    # Try to restore from cached cookies
    mb = cache.get("mailboxes", {}).get(email_key, {})
    saved_cookies = mb.get("mohmal_cookies", {})
    if saved_cookies:
        dbg(f"mohmal: restoring session from cached cookies for {email_key}")
        s = _restore_session(saved_cookies)
        _mohmal_pool[email_key] = {"session": s}
        return s

    raise RuntimeError(f"mohmal: no active session for {email_key}. Run --mail-id @emailinbo.live first.")


def mohmal_list_messages(email_key: str, cache: dict) -> list[dict]:
    """
    GET /en/refresh → scrape inbox table rows.
    Returns list of {id, subject, sender, time}.
    """
    s = mohmal_get_session(email_key, cache)
    resp = s.get(MOHMAL_BASE + "/en/refresh", timeout=HTTP_TIMEOUT, allow_redirects=True)
    dbg(f"mohmal: GET /en/refresh -> {resp.status_code}")
    if resp.status_code != 200:
        raise RuntimeError(f"mohmal: /en/refresh failed (HTTP {resp.status_code})")
    return _scrape_messages(resp.text)


def mohmal_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    """
    GET /en/message/<id> → raw HTML body of message.
    Returns {id, body_html}.
    """
    s = mohmal_get_session(email_key, cache)
    resp = s.get(f"{MOHMAL_BASE}/en/message/{msg_id}", timeout=HTTP_TIMEOUT)
    dbg(f"mohmal: GET /en/message/{msg_id} -> {resp.status_code} len={len(resp.text)}")
    if resp.status_code != 200:
        raise RuntimeError(f"mohmal: /en/message/{msg_id} failed (HTTP {resp.status_code})")
    return {"id": msg_id, "body_html": resp.text}


def mohmal_delete_session(email_key: str, cache: dict):
    """
    GET /en/logout → deletes server session + inbox.
    No per-message delete available.
    """
    try:
        s = mohmal_get_session(email_key, cache)
        resp = s.get(MOHMAL_BASE + "/en/logout", timeout=HTTP_TIMEOUT, allow_redirects=True)
        dbg(f"mohmal: GET /en/logout -> {resp.status_code}")
    except Exception:
        pass
    _mohmal_pool.pop(email_key, None)
