#!/usr/bin/env python3
"""
cli_mailinator.py - mailinator.com client logic for the unimail.py CLI.

API PROTOCOL (mailinator.com) — public REST API, no API key required for
public @mailinator.com inboxes.

  base: https://www.mailinator.com
  docs: https://manybrain.github.io/m8r-rest-api/

  PUBLIC (no-auth) FLOW:
    1. GET /api/v2/domains/mailinator.com/inboxes/<inbox>
       → {msgs: [{id, from, subject, time, seconds_ago, ...}]}
       'inbox' is the username part of the email address (case-insensitive).

    2. GET /api/v2/domains/mailinator.com/inboxes/<inbox>/messages/<id>
       → {id, from, subject, parts: [{mime-type, body}], headers, ...}
       Full message with parts; look for text/html or text/plain part.

  NOTES:
    - No authentication needed for @mailinator.com public inboxes.
    - Other domains (e.g. @maildrop.cc) require an API key — not used here.
    - Mailinator trims messages after ~48–72 hours.
    - Any username is valid — the inbox is publicly readable.
    - We use 'mailinator.com' as the only domain (no aliases needed).
    - No session to maintain; every call is stateless.

SESSION MODEL:
  Stateless — no login, no session token. Each call directly queries the inbox
  by username. We cache the message list after --list-message for --view-message.
"""

from curl_cffi import requests as curl_requests

from cli_config import dbg, IMPERSONATE, HTTP_TIMEOUT

MAILINATOR_API = "https://api.mailinator.com"
MAILINATOR_DOMAIN = "public"  # public domain — no API key needed


def _mailinator_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://www.mailinator.com/",
    })
    return s


def mailinator_list_messages(inbox: str) -> list[dict]:
    """
    GET /api/v2/domains/mailinator.com/inboxes/<inbox>
    Returns list of message summaries sorted newest-first.
    inbox = username part of the email (e.g. 'testclaude' for testclaude@mailinator.com).
    """
    s = _mailinator_session()
    url = f"{MAILINATOR_API}/api/v2/domains/{MAILINATOR_DOMAIN}/inboxes/{inbox}"
    dbg(f"mailinator: GET {url}")
    resp = s.get(url, timeout=HTTP_TIMEOUT)
    dbg(f"mailinator: -> {resp.status_code}  body={resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"mailinator: list failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    body = resp.json()
    return body.get("msgs", [])


def mailinator_get_message(inbox: str, msg_id: str) -> dict:
    """
    GET /api/v2/domains/mailinator.com/inboxes/<inbox>/messages/<id>
    Returns full message with parts.
    """
    s = _mailinator_session()
    url = f"{MAILINATOR_API}/api/v2/domains/{MAILINATOR_DOMAIN}/inboxes/{inbox}/messages/{msg_id}"
    dbg(f"mailinator: GET {url}")
    resp = s.get(url, timeout=HTTP_TIMEOUT)
    dbg(f"mailinator: -> {resp.status_code}  body={resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"mailinator: get message failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    return resp.json()


def mailinator_extract_body(msg: dict) -> str:
    """
    Extract the best body text from a full message dict.
    Prefers text/html, falls back to text/plain.
    """
    parts = msg.get("parts", [])
    html_body = ""
    plain_body = ""
    for part in parts:
        mime = part.get("headers", {}).get("content-type", "")
        body = part.get("body", "")
        if "text/html" in mime and not html_body:
            html_body = body
        elif "text/plain" in mime and not plain_body:
            plain_body = body
    return html_body or plain_body or ""
