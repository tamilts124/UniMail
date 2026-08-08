#!/usr/bin/env python3
"""
cli_maildrop.py - maildrop.cc client logic for the unimail.py CLI.

API PROTOCOL (maildrop.cc) — public GraphQL API, no authentication required.

  base: https://api.maildrop.cc/graphql
  docs: https://github.com/m242/maildrop (open-source)

  FLOW:
    1. Query inbox (list messages):
       POST https://api.maildrop.cc/graphql
       { "query": "{ inbox(mailbox: \"<inbox>\") { id from subject date } }" }
       → { data: { inbox: [{id, from, subject, date, ...}] } }

    2. Query single message (full body):
       POST https://api.maildrop.cc/graphql
       { "query": "{ message(mailbox: \"<inbox>\", id: \"<id>\") { id from subject date html } }" }
       → { data: { message: {id, from, subject, date, html, headerfrom, ...} } }

    3. Mutation: delete message:
       POST https://api.maildrop.cc/graphql
       { "query": "mutation { delete(mailbox: \"<inbox>\", id: \"<id>\") }" }

  NOTES:
    - mailbox = username part of the address (e.g. 'testclaude' for testclaude@maildrop.cc).
    - Domain is always maildrop.cc (the only one supported).
    - No session/auth needed. Stateless.
    - Inbox is publicly readable by anyone who knows the address.
    - Messages expire after ~1 hour.

SESSION MODEL:
  Fully stateless — each call creates a new HTTP request. No cache entry needed
  beyond the message list cached after --list-message.
"""

from curl_cffi import requests as curl_requests

from cli_config import dbg, IMPERSONATE, HTTP_TIMEOUT

MAILDROP_API = "https://api.maildrop.cc/graphql"
MAILDROP_DOMAIN = "maildrop.cc"


def _maildrop_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update({
        "Accept":          "application/json",
        "Content-Type":    "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://maildrop.cc/",
        "Origin":          "https://maildrop.cc",
    })
    return s


def _maildrop_query(query: str) -> dict:
    s = _maildrop_session()
    payload = {"query": query}
    dbg(f"maildrop: POST graphql query={query[:120]!r}")
    resp = s.post(MAILDROP_API, json=payload, timeout=HTTP_TIMEOUT)
    dbg(f"maildrop: -> {resp.status_code}  body={resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"maildrop: GraphQL request failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    body = resp.json()
    if "errors" in body:
        raise RuntimeError(f"maildrop: GraphQL errors: {body['errors']}")
    return body.get("data", {})


def maildrop_list_messages(inbox: str) -> list[dict]:
    """
    Query inbox(mailbox) to get message list.
    inbox = username part of the email.
    """
    query = f'{{ inbox(mailbox: "{inbox}") {{ id mailfrom headerfrom subject date }} }}'
    data = _maildrop_query(query)
    return data.get("inbox", []) or []


def maildrop_get_message(inbox: str, msg_id: str) -> dict:
    """
    Query message(mailbox, id) to get full message with html body.
    """
    query = (
        f'{{ message(mailbox: "{inbox}", id: "{msg_id}") '
        f'{{ id mailfrom headerfrom subject date html }} }}'
    )
    data = _maildrop_query(query)
    return data.get("message") or {}


def maildrop_delete_message(inbox: str, msg_id: str) -> bool:
    """
    Mutation: delete(mailbox, id).
    Returns True if deletion appears successful.
    """
    query = f'mutation {{ delete(mailbox: "{inbox}", id: "{msg_id}") }}'
    try:
        data = _maildrop_query(query)
        return True
    except Exception:
        return False
