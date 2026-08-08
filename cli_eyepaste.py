#!/usr/bin/env python3
"""
cli_eyepaste.py - eyepaste.com client logic for the unimail.py CLI.

API PROTOCOL (eyepaste.com) — RSS-based stateless inbox, no auth required.
  Base: https://www.eyepaste.com

  The service is fully stateless — any username@eyepaste.com is a valid inbox.
  Email is delivered normally (MX record active, Gmail-deliverable confirmed).
  Messages expire after 1 hour and are publicly readable.

  ENDPOINTS:
    GET /inbox/<email>.rss
      → RSS XML with <item> elements per message.
      Each <item> has:
        <title><![CDATA[ sender: subject ]]></title>
        <description><![CDATA[
          <p>From: ... <br/> To: ... <br/> Subject: ... <br/> Date: ... </p>
          <p>Body text</p>
        ]]></description>
        <pubdate>Mon, 20 Jul 2026 19:49:48 -0700</pubdate>

  NOTES:
    - Domain: eyepaste.com (only one domain)
    - No delete endpoint — emails auto-expire after 1 hour
    - Inbox is publicly readable by anyone who knows the address
    - No per-message ID — uses index 1..N from RSS feed order
    - Full body (HTML) is embedded in the RSS <description> CDATA
    - Blocked by Cloudflare when using plain urllib; use curl_cffi

SESSION MODEL:
  Fully stateless — no cache entry needed beyond the message list.
"""

import re
import html
from curl_cffi import requests as curl_requests

from cli_config import dbg, IMPERSONATE, HTTP_TIMEOUT

EYEPASTE_BASE   = "https://www.eyepaste.com"
EYEPASTE_DOMAIN = "eyepaste.com"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _eyepaste_session() -> curl_requests.Session:
    s = curl_requests.Session(impersonate=IMPERSONATE)
    s.headers.update(_HDR)
    return s


def _parse_cdata(text: str) -> str:
    """Extract content from <![CDATA[ ... ]]> if present."""
    m = re.search(r'<!\[CDATA\[(.*?)\]\]>', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def _parse_rss_items(xml: str) -> list[dict]:
    """
    Parse RSS XML and return list of message dicts:
      id, from, subject, date, body_html
    Uses sequential index as id (1-based string) since eyepaste has no message IDs.
    """
    items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL | re.IGNORECASE)
    messages = []
    for idx, item in enumerate(items, 1):
        # Extract title ("sender: subject")
        title_m = re.search(r'<title>(.*?)</title>', item, re.DOTALL | re.IGNORECASE)
        title_raw = _parse_cdata(title_m.group(1)) if title_m else ""

        # Extract description (full HTML body with headers)
        desc_m = re.search(r'<description>(.*?)</description>', item, re.DOTALL | re.IGNORECASE)
        desc_raw = _parse_cdata(desc_m.group(1)) if desc_m else ""

        # Extract pubdate
        date_m = re.search(r'<pubdate>(.*?)</pubdate>', item, re.DOTALL | re.IGNORECASE)
        date_str = date_m.group(1).strip() if date_m else ""

        # Parse from/subject from title (format: "from_addr: subject")
        from_addr = ""
        subject = title_raw
        if ": " in title_raw:
            from_addr, subject = title_raw.split(": ", 1)
            from_addr = from_addr.strip()
            subject   = subject.strip()

        # If from_addr not in title, try to extract from description HTML
        if not from_addr:
            fm = re.search(r'From:\s*([\w.@+<>\s\'"!#$%-]+?)\s*<br', desc_raw, re.IGNORECASE)
            if fm:
                from_addr = fm.group(1).strip()

        messages.append({
            "id":        str(idx),
            "from":      from_addr or "unknown",
            "subject":   subject or "(no subject)",
            "date":      date_str,
            "body_html": desc_raw,
        })

    return messages


def eyepaste_list_messages(email: str) -> list[dict]:
    """
    Fetch RSS feed for `email` and return parsed message list.
    email = full email address, e.g. testclaude@eyepaste.com
    """
    rss_url = f"{EYEPASTE_BASE}/inbox/{email}.rss"
    dbg(f"eyepaste: GET {rss_url}")
    s = _eyepaste_session()
    resp = s.get(rss_url, timeout=HTTP_TIMEOUT)
    dbg(f"eyepaste: -> {resp.status_code}  len={len(resp.text)}")
    if resp.status_code != 200:
        raise RuntimeError(
            f"eyepaste: list_messages failed (HTTP {resp.status_code}): {resp.text[:200]}"
        )
    return _parse_rss_items(resp.text)


def eyepaste_get_message(email: str, msg_index: str) -> dict:
    """
    Re-fetch the RSS feed and return the message at position `msg_index` (1-based).
    eyepaste has no per-message endpoint — body is embedded in the RSS feed.
    """
    messages = eyepaste_list_messages(email)
    idx = int(msg_index) - 1
    if 0 <= idx < len(messages):
        return messages[idx]
    return {}
