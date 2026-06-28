#!/usr/bin/env python3
"""
cli_tms.py - tempmailsall.com client logic for the unimail.py CLI.
Uses WordPress admin-ajax endpoints.
"""

import json
import re
import time
from curl_cffi import requests as curl_requests

from cli_config import dbg, save_cache, IMPERSONATE, HTTP_TIMEOUT

# in-process session pool: email_key -> {"session": Session, "session_id": str, "nonce": str}
_tms_pool: dict[str, dict] = {}
TMS_BASE = "https://tempmailsall.com"


def _tms_new_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         TMS_BASE + "/",
        "Origin":          TMS_BASE,
    })
    return s


def _tms_scrape_config(s: curl_requests.Session) -> tuple[str, list[str]]:
    """GET homepage, scrape nonce and domains from TempMailPro JS object."""
    dbg(f"tms: GET {TMS_BASE}/ ...")
    resp = s.get(TMS_BASE + "/", timeout=HTTP_TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"tempmailsall: failed to GET homepage (HTTP {resp.status_code})")
    
    # Search for nonce inside TempMailPro JS object specifically
    nonce_match = re.search(r'TempMailPro\s*=\s*\{[^}]+?"nonce"\s*:\s*"([a-f0-9]+)"', resp.text)
    nonce = nonce_match.group(1) if nonce_match else ""
    
    # Search for domains
    domains_match = re.search(r'"domains"\s*:\s*\[([^\]]+)\]', resp.text)
    domains = []
    if domains_match:
        domains = [d.strip('"\' ') for d in domains_match.group(1).split(',')]
        
    dbg(f"tms: scraped nonce={nonce!r} domains={domains!r}")
    return nonce, domains


def _tms_post(s: curl_requests.Session, data: dict) -> dict:
    url = f"{TMS_BASE}/wp-admin/admin-ajax.php"
    dbg(f"tms: POST /wp-admin/admin-ajax.php payload={data!r}")
    resp = s.post(url, data=data, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    dbg(f"tms: POST -> success={body.get('success')} body={str(body)[:200]}...")
    return body


def _tms_save(email_key: str, session_id: str, nonce: str, address_id: int, expires_at: str, cache: dict):
    mb = cache["mailboxes"].setdefault(email_key, {})
    mb["session_id"] = session_id
    mb["nonce"] = nonce
    mb["address_id"] = address_id
    mb["expires_at"] = expires_at
    save_cache(cache)


def _tms_get_session(email_key: str, cache: dict) -> tuple[curl_requests.Session, str, str, str]:
    """
    Return (session, session_id, nonce, real_address).
    1. Check in-process pool.
    2. Try restoring from cache and validating.
    3. Scrape new nonce, call tmpmp_generate_email to register/create.
    """
    if email_key in _tms_pool:
        p = _tms_pool[email_key]
        return p["session"], p["session_id"], p["nonce"], email_key

    mb = cache["mailboxes"].get(email_key, {})
    saved_sid = mb.get("session_id", "")
    saved_nonce = mb.get("nonce", "")

    s = _tms_new_session()

    if saved_sid and saved_nonce:
        dbg(f"tms: validating cached session for {email_key} ...")
        # Validate using get_inbox
        t = int(time.time() * 1000)
        body = _tms_post(s, {
            "action": "tmpmp_get_inbox",
            "nonce": saved_nonce,
            "address": email_key,
            "_t": t
        })
        if body.get("success"):
            _tms_pool[email_key] = {"session": s, "session_id": saved_sid, "nonce": saved_nonce}
            return s, saved_sid, saved_nonce, email_key
        dbg("tms: validation failed - getting fresh session")

    # Scrape nonce & domains
    nonce, domains = _tms_scrape_config(s)
    if not nonce:
        raise RuntimeError("tempmailsall: could not scrape nonce from homepage HTML")

    user, domain = email_key.split("@", 1)
    
    # Generate/Register email
    body = _tms_post(s, {
        "action": "tmpmp_generate_email",
        "nonce": nonce,
        "session_id": "",
        "domain": domain,
        "username": user
    })
    
    if not body.get("success") or "data" not in body:
        raise RuntimeError(f"tempmailsall: generate_email failed: {body}")
        
    data = body["data"]
    real_address = data.get("address", email_key)
    session_id = data.get("session_id", "")
    address_id = data.get("address_id", 0)
    expires_at = data.get("expires_at", "")
    
    # Save using real_address
    _tms_pool[real_address] = {"session": s, "session_id": session_id, "nonce": nonce}
    _tms_save(real_address, session_id, nonce, address_id, expires_at, cache)

    # Save mock ID redirect mapping
    if real_address != email_key:
        cache["mailboxes"][email_key] = {"redirect_to": real_address}
        save_cache(cache)
    
    return s, session_id, nonce, real_address


def tms_list_mails(email_key: str, cache: dict) -> dict:
    s, _, nonce, _ = _tms_get_session(email_key, cache)
    t = int(time.time() * 1000)
    body = _tms_post(s, {
        "action": "tmpmp_get_inbox",
        "nonce": nonce,
        "address": email_key,
        "_t": t
    })
    return body


def tms_get_message(email_key: str, msg_id: str, cache: dict) -> dict:
    s, _, nonce, _ = _tms_get_session(email_key, cache)
    body = _tms_post(s, {
        "action": "tmpmp_get_email",
        "nonce": nonce,
        "email_id": msg_id,
        "address": email_key
    })
    return body


def tms_delete_mailbox(email_key: str, cache: dict):
    try:
        s, session_id, nonce, _ = _tms_get_session(email_key, cache)
        _tms_post(s, {
            "action": "tmpmp_delete_inbox",
            "nonce": nonce,
            "address": email_key,
            "session_id": session_id
        })
    except Exception as e:
        dbg(f"tms: delete on server failed ({e})")
    
    _tms_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
        save_cache(cache)
