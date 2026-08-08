#!/usr/bin/env python3
"""Debug fakemail.net session init."""
import re, sys
from curl_cffi import requests as curl_requests

BASE = "https://www.fakemail.net"
AJAX = {"X-Requested-With": "XMLHttpRequest"}

s = curl_requests.Session(impersonate="chrome124")
s.headers.update({"Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
                   "Referer": BASE + "/", "Origin": BASE})

print("GET /", flush=True)
r = s.get(BASE + "/", timeout=20)
print(f"status: {r.status_code}", flush=True)
print(f"body length: {len(r.text)}", flush=True)

# Try all CSRF patterns
patterns = [
    r'const\s+CSRF\s*=\s*["\']([^"\']+)["\']',
    r'csrf[_-]?token["\s:=]+["\']([a-zA-Z0-9_\-]+)["\']',
    r'CSRF["\s:=]+["\']([a-zA-Z0-9_\-]+)["\']',
    r'"_token"\s*:\s*"([^"]+)"',
    r"name=['\"]_token['\"] value=['\"]([^'\"]+)['\"]",
]
csrf = ""
for p in patterns:
    m = re.search(p, r.text, re.IGNORECASE)
    if m:
        csrf = m.group(1)
        print(f"CSRF found by pattern: {p[:50]}")
        print(f"CSRF value: {csrf[:50]}")
        break
if not csrf:
    print("NO CSRF FOUND in page!")
    # Print a snippet of the page
    print("Page snippet (200-400 chars):", r.text[200:500])

print("Cookies:", dict(s.cookies), flush=True)
print()

if csrf:
    print(f"GET /index/index?csrf_token={csrf[:10]}...", flush=True)
    r2 = s.get(f"{BASE}/index/index?csrf_token={csrf}", headers=AJAX, timeout=20)
    print(f"status: {r2.status_code}", flush=True)
    print(f"Content-Type: {r2.headers.get('Content-Type', '')}", flush=True)
    print(f"Body: {r2.text[:500]}", flush=True)

print("\nGET /index/refresh", flush=True)
r3 = s.get(f"{BASE}/index/refresh", headers=AJAX, timeout=20)
print(f"status: {r3.status_code}", flush=True)
print(f"Body: {r3.text[:300]}", flush=True)
