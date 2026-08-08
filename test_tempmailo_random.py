#!/usr/bin/env python3
"""Test if POST / works with any random address (not just server-assigned ones)."""
import re, sys
from curl_cffi import requests as curl_requests
import random, string

BASE = "https://tempmailo.com"
DOMAINS = ["denipl.net", "fxzig.com"]

# Make up a random address
user = ''.join(random.choices(string.ascii_lowercase, k=8))
domain = random.choice(DOMAINS)
test_addr = f"{user}@{domain}"
print(f"Testing with made-up address: {test_addr}", flush=True)

s = curl_requests.Session(impersonate="chrome124")
resp = s.get(BASE + "/", timeout=20)
print(f"GET / status: {resp.status_code}", flush=True)

m = re.search(r'<input[^>]+name=["\']__RequestVerificationToken["\'][^>]+value=["\']([^"\']+)["\']', resp.text)
if not m:
    m = re.search(r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']__RequestVerificationToken["\']', resp.text)
token = m.group(1) if m else ""
print(f"Token: {'OK' if token else 'MISSING'}", flush=True)

resp2 = s.post(
    BASE + "/",
    json={"mail": test_addr},
    headers={
        "RequestVerificationToken": token,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    },
    timeout=20,
)
print(f"POST / status: {resp2.status_code}", flush=True)
print(f"POST / body: {resp2.text[:300]!r}", flush=True)
