#!/usr/bin/env python3
"""
cli_maildax.py - maildax.cc client logic for the unimail.py CLI.
(Placeholder — full command wiring deferred, same as original.)
"""

import urllib.parse
from curl_cffi import requests as curl_requests

from cli_config import MAILDAX_BASE, IMPERSONATE, HTTP_TIMEOUT

_maildax_session = None

def _maildax_get_session():
    global _maildax_session
    if _maildax_session is None:
        s = curl_requests.Session(impersonate=IMPERSONATE)
        s.headers.update({
            "Accept":          "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer":         MAILDAX_BASE + "/",
            "Origin":          MAILDAX_BASE,
        })
        _maildax_session = s
    return _maildax_session

def _maildax_xsrf_from_session(s) -> str:
    raw = s.cookies.get("XSRF-TOKEN")
    return urllib.parse.unquote(raw) if raw else ""

def maildax_fetch_csrf() -> tuple[str, str]:
    s = _maildax_get_session()
    resp = s.get(MAILDAX_BASE + "/", timeout=HTTP_TIMEOUT)
    return _maildax_xsrf_from_session(s), resp.text

def maildax_post(endpoint: str, data: dict, xsrf: str) -> tuple[dict, str]:
    s = _maildax_get_session()
    headers = {"x-xsrf-token": xsrf} if xsrf else {}
    resp = s.post(MAILDAX_BASE + endpoint, json=data, headers=headers, timeout=HTTP_TIMEOUT)
    if resp.status_code == 419:
        xsrf, _ = maildax_fetch_csrf()
        resp = s.post(MAILDAX_BASE + endpoint, json=data,
                      headers={"x-xsrf-token": xsrf}, timeout=HTTP_TIMEOUT)
    try:
        body = resp.json()
    except Exception:
        body = {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    return body, _maildax_xsrf_from_session(s) or xsrf
