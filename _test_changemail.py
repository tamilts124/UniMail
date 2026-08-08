#!/usr/bin/env python3
"""Test /changemail endpoint directly to understand what it returns."""
import sys, os, random
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
os.chdir(r'D:\ClaudeDir\tempmail')

from curl_cffi import requests as curl_requests
from cli_config import IMPERSONATE, HTTP_TIMEOUT

BASE = "https://tempmailo.com"
s = curl_requests.Session(impersonate=IMPERSONATE)
s.headers.update({
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE + "/",
    "Origin": BASE,
})

# Step 1: GET / to get cookie + antiforgery token
print("Step 1: GET /", flush=True)
r = s.get(BASE + "/", timeout=HTTP_TIMEOUT)
print(f"  Status: {r.status_code}", flush=True)

import re
m = re.search(r'<input[^>]+name=["\']__RequestVerificationToken["\'][^>]+value=["\']([^"\']+)["\']', r.text)
if not m:
    m = re.search(r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']__RequestVerificationToken["\']', r.text)
token = m.group(1) if m else ""
print(f"  Token: {token[:40] if token else 'NOT FOUND'}", flush=True)

# Step 2: GET /changemail?_r=<random>
rand = random.random()
url = f"{BASE}/changemail?_r={rand}"
print(f"\nStep 2: GET /changemail?_r={rand:.5f}", flush=True)
r2 = s.get(url, headers={
    "RequestVerificationToken": token,
    "Accept": "text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
}, timeout=HTTP_TIMEOUT)
print(f"  Status: {r2.status_code}", flush=True)
print(f"  Body: {r2.text[:300]}", flush=True)
print(f"  Content-Type: {r2.headers.get('content-type','?')}", flush=True)
