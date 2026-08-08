#!/usr/bin/env python3
"""Test tempmailo.com POST / with curl_cffi using a known address."""
import random, re, sys

BASE = "https://tempmailo.com"

# Address we know exists from browser session
KNOWN_ADDR = "qizyhetu@denipl.net"

from curl_cffi import requests as curl_requests

s = curl_requests.Session(impersonate="chrome124")
s.headers.update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
    "Origin": BASE,
})

print("Step 1: GET / to get token + cookies...", flush=True)
resp = s.get(BASE + "/", timeout=20)
print(f"  Status: {resp.status_code}", flush=True)

m = re.search(r'<input[^>]+name=["\']__RequestVerificationToken["\'][^>]+value=["\']([^"\']+)["\']', resp.text)
if not m:
    m = re.search(r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']__RequestVerificationToken["\']', resp.text)
token = m.group(1) if m else ""
print(f"  Token: {token[:30]}..." if token else "  Token: NONE", flush=True)

if not token:
    print("FAIL: no token", flush=True)
    sys.exit(1)

print("Step 2: POST / with known addr to check inbox...", flush=True)
resp2 = s.post(
    BASE + "/",
    json={"mail": KNOWN_ADDR},
    headers={
        "RequestVerificationToken": token,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    },
    timeout=20,
)
print(f"  Status: {resp2.status_code}", flush=True)
print(f"  Body: {resp2.text[:300]!r}", flush=True)
