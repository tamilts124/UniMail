#!/usr/bin/env python3
"""Debug tempmailo.com - test what's happening with curl_cffi."""
import random
import sys

TEMPMAILO_COM_BASE = "https://tempmailo.com"

# Step 1: Try with curl_cffi
try:
    from curl_cffi import requests as curl_requests
    print("curl_cffi available", flush=True)
    
    s = curl_requests.Session(impersonate="chrome124")
    s.headers.update({
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    
    print("GET /...", flush=True)
    resp = s.get(TEMPMAILO_COM_BASE + "/", timeout=20)
    print(f"  Status: {resp.status_code}", flush=True)
    print(f"  Cookies: {dict(s.cookies)}", flush=True)
    
    # Find token
    import re
    m = re.search(r'<input[^>]+name=["\']__RequestVerificationToken["\'][^>]+value=["\']([^"\']+)["\']', resp.text)
    if not m:
        m = re.search(r'<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']__RequestVerificationToken["\']', resp.text)
    token = m.group(1) if m else ""
    print(f"  Token found: {bool(token)} - {token[:30] if token else 'NONE'}", flush=True)
    
    if token:
        rand = str(random.random())
        url = f"{TEMPMAILO_COM_BASE}/changemail?_r={rand}"
        print(f"GET /changemail?_r=... ...", flush=True)
        resp2 = s.get(url, headers={"RequestVerificationToken": token}, timeout=20)
        print(f"  Status: {resp2.status_code}", flush=True)
        print(f"  Body: {resp2.text[:200]!r}", flush=True)
    else:
        print("HTML snippet:", resp.text[:500], flush=True)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback; traceback.print_exc()
