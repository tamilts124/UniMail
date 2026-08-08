#!/usr/bin/env python3
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from curl_cffi import requests as curl_requests
from cli_config import IMPERSONATE, HTTP_TIMEOUT

FAKEMAIL_BASE = "https://www.fakemail.net"
AJAX = {"X-Requested-With": "XMLHttpRequest"}

s = curl_requests.Session(impersonate=IMPERSONATE)
s.headers.update({
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": FAKEMAIL_BASE + "/",
})

# Step 1: GET homepage
print("Step 1: GET /", flush=True)
r = s.get(FAKEMAIL_BASE + "/", timeout=HTTP_TIMEOUT)
print(f"  status={r.status_code}, len={len(r.text)}", flush=True)

# Extract CSRF
m = re.search(r'const\s+CSRF\s*=\s*["\']([^"\']+)["\']', r.text)
csrf = m.group(1) if m else ""
print(f"  CSRF={csrf!r}", flush=True)

# Check cookies
print(f"  cookies: {dict(s.cookies)}", flush=True)

if not csrf:
    # Try alternative patterns
    for pat in [r'csrf["\s:=]+([a-f0-9]{40,})', r'"csrf"\s*:\s*"([^"]+)"', r'CSRF\s*=\s*"([^"]+)"']:
        m2 = re.search(pat, r.text, re.I)
        if m2:
            print(f"  alt CSRF pattern found: {m2.group(1)[:20]}", flush=True)
            csrf = m2.group(1)
            break
    if not csrf:
        print("  CSRF not found in page! Dumping first 2000 chars:", flush=True)
        print(r.text[:2000], flush=True)

if csrf:
    # Step 2: /index/index
    print(f"\nStep 2: GET /index/index?csrf_token={csrf[:10]}...", flush=True)
    r2 = s.get(f"{FAKEMAIL_BASE}/index/index?csrf_token={csrf}", headers=AJAX, timeout=HTTP_TIMEOUT)
    print(f"  status={r2.status_code}", flush=True)
    print(f"  content-type={r2.headers.get('content-type','?')}", flush=True)
    print(f"  raw body (first 500): {repr(r2.text[:500])}", flush=True)
    
    # Try parsing
    try:
        j = r2.json()
        print(f"  JSON OK: {j}", flush=True)
    except Exception as e:
        print(f"  JSON parse error: {e}", flush=True)
        # check for BOM
        raw = r2.content
        print(f"  first 10 bytes: {raw[:10]}", flush=True)

print("DONE", flush=True)
