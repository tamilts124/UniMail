#!/usr/bin/env python3
"""
cli_1secmail.py - 1secmail.com client logic for the unimail.py CLI.

API PROTOCOL (1secmail.com) — Public REST API, fully stateless, no auth needed.
  Base: https://www.1secmail.com/api/v1/
  Reference: https://www.1secmail.com/api/

  The service is entirely stateless — any username@<supported_domain> is a valid
  inbox. No session creation or authentication is required.

  ENDPOINTS:
    GET /api/v1/?action=genRandomMailbox&count=1
      → ["randomuser@1secmail.com"]
      Generates a random address; optional, any address works without this.

    GET /api/v1/?action=getDomainList
      → ["1secmail.com", "1secmail.org", "1secmail.net", "wwjmp.com",
          "esiix.com", "xojxe.com", "yoggm.com"]
      Returns available domains.

    GET /api/v1/?action=getMessages&login=<user>&domain=<domain>
      → [{id, from, subject, date}, ...]
      Lists messages in the inbox.

    GET /api/v1/?action=readMessage&login=<user>&domain=<domain>&id=<id>
      → {id, from, subject, date, attachments, body, textBody, htmlBody}
      Reads a single message (full body).

    GET /api/v1/?action=download&login=<user>&domain=<domain>&id=<id>&file=<filename>
      Downloads an attachment.

  SESSION MODEL:
    Fully stateless — no cache entry needed. Just username + domain.
    Any username can be used; the domain must be one of the supported domains.
"""

import requests

from cli_config import dbg, HTTP_TIMEOUT

ONESECMAIL_BASE = "https://www.1secmail.com/api/v1/"
ONESECMAIL_SITE = "1secmail.com"

# Domains known to work (fetched dynamically via getDomainList, fallback here)
ONESECMAIL_DOMAINS = [
    "1secmail.com",
    "1secmail.org",
    "1secmail.net",
    "wwjmp.com",
    "esiix.com",
    "xojxe.com",
    "yoggm.com",
]


def onesecmail_get_domains() -> list[str]:
    """Fetch the current list of supported domains from the API."""
    try:
        resp = requests.get(
            ONESECMAIL_BASE,
            params={"action": "getDomainList"},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 200:
            domains = resp.json()
            if isinstance(domains, list) and domains:
                return domains
    except Exception as e:
        dbg(f"1secmail: getDomainList failed: {e}")
    return ONESECMAIL_DOMAINS


def onesecmail_gen_random_address() -> str:
    """Generate a random address from the API."""
    try:
        resp = requests.get(
            ONESECMAIL_BASE,
            params={"action": "genRandomMailbox", "count": 1},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json()
            if isinstance(result, list) and result:
                return result[0]
    except Exception as e:
        dbg(f"1secmail: genRandomMailbox failed: {e}")
    import random, string
    user = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{user}@1secmail.com"


def onesecmail_list_messages(login: str, domain: str) -> list[dict]:
    """
    GET /api/v1/?action=getMessages&login=<login>&domain=<domain>
    Returns list of message summaries [{id, from, subject, date}, ...].
    """
    dbg(f"1secmail: getMessages login={login} domain={domain}")
    resp = requests.get(
        ONESECMAIL_BASE,
        params={"action": "getMessages", "login": login, "domain": domain},
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"1secmail: getMessages -> {resp.status_code} {resp.text[:200]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"1secmail: getMessages failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    result = resp.json()
    if isinstance(result, list):
        return result
    return []


def onesecmail_get_message(login: str, domain: str, msg_id: str) -> dict:
    """
    GET /api/v1/?action=readMessage&login=<login>&domain=<domain>&id=<id>
    Returns full message {id, from, subject, date, body, textBody, htmlBody, attachments}.
    """
    dbg(f"1secmail: readMessage login={login} domain={domain} id={msg_id}")
    resp = requests.get(
        ONESECMAIL_BASE,
        params={"action": "readMessage", "login": login, "domain": domain, "id": msg_id},
        timeout=HTTP_TIMEOUT,
    )
    dbg(f"1secmail: readMessage -> {resp.status_code} {resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"1secmail: readMessage failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    return resp.json()
