#!/usr/bin/env python3
"""
cli_tempmail_plus.py - tempmail.plus client logic for the unimail.py CLI.

API PROTOCOL (tempmail.plus) — internal REST API, no auth, stateless.
  Base: https://tempmail.plus
  Implemented: 2026-07-20 session-5.

  The address is user-chosen; any username@mailto.plus works.
  An optional PIN (epin) can protect the inbox, left empty for public access.

  ENDPOINTS:
    GET /api/mails?email=USER@mailto.plus&first_id=0&epin=
      → {count, first_id, last_id, limit, mail_list:[{mail_id, subject,
             from_mail, from_name, time, is_new}], more, result}
      Lists all messages. first_id=0 returns from the start.

    GET /api/mails?email=USER@mailto.plus&first_id=LAST_ID&epin=
      Poll for new messages after last_id.

    GET /api/mail/{mail_id}?email=USER@mailto.plus&epin=
      → {mail_id, from_mail, from_name, subject, html, text, time, attachments}
      Fetch full message body.

    DELETE /api/mail/{mail_id}?email=USER@mailto.plus&epin=
      → {result: true} on success.

  DOMAIN: mailto.plus (the only domain)
  SESSION MODEL: Fully stateless. Address is user-chosen.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

TEMPMAILPLUS_BASE   = "https://tempmail.plus"
TEMPMAILPLUS_SITE   = "tempmail.plus"
TEMPMAILPLUS_DOMAIN = "mailto.plus"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://tempmail.plus/",
    "Origin":  "https://tempmail.plus",
}


def tempmailplus_list_messages(email: str, first_id: int = 0, epin: str = "") -> list[dict]:
    """
    GET /api/mails?email=EMAIL&first_id=FIRST_ID&epin=EPIN
    Returns list of message summaries.
    """
    dbg(f"tempmailplus: list_messages email={email!r}")
    r = requests.get(
        f"{TEMPMAILPLUS_BASE}/api/mails",
        params={"email": email, "first_id": first_id, "epin": epin},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"tempmailplus: list_messages -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"tempmailplus: list_messages failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    data = r.json()
    if not data.get("result"):
        return []
    return data.get("mail_list", [])


def tempmailplus_get_message(email: str, mail_id: str, epin: str = "") -> dict:
    """
    GET /api/mail/{mail_id}?email=EMAIL&epin=EPIN
    Returns full message with html/text body.
    """
    dbg(f"tempmailplus: get_message id={mail_id!r}")
    r = requests.get(
        f"{TEMPMAILPLUS_BASE}/api/mail/{mail_id}",
        params={"email": email, "epin": epin},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"tempmailplus: get_message -> {r.status_code} {r.text[:200]}")
    if r.status_code != 200:
        raise RuntimeError(
            f"tempmailplus: get_message failed (HTTP {r.status_code}): {r.text[:200]}"
        )
    return r.json()


def tempmailplus_delete_message(email: str, mail_id: str, epin: str = "") -> bool:
    """
    DELETE /api/mail/{mail_id}?email=EMAIL&epin=EPIN
    Returns True on success.
    """
    dbg(f"tempmailplus: delete_message id={mail_id!r}")
    r = requests.delete(
        f"{TEMPMAILPLUS_BASE}/api/mail/{mail_id}",
        params={"email": email, "epin": epin},
        headers=_HDR,
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"tempmailplus: delete_message -> {r.status_code}")
    return r.status_code in (200, 204) and r.json().get("result", False)
