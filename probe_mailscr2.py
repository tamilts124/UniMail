#!/usr/bin/env python3
"""Deep probe of mailscr.us - checking the correct API endpoints."""
from curl_cffi import requests as cr
import json, sys, re

s = cr.Session(impersonate='chrome120')
s.headers.update({'Accept': 'application/json, */*'})

base = 'https://mailscr.us'

# Get the main JS bundle to find API routes
r = s.get(base + '/', timeout=10)
html = r.text

# Find script sources
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
print('Scripts:', scripts[:10])

# Check the stats endpoint
for path in ['/api/public/stats', '/api/customer/plans']:
    try:
        r2 = s.get(base + path, timeout=8)
        print(f'GET {path} -> {r2.status_code} ct={r2.headers.get("content-type","")} len={len(r2.text)}')
        print(' ', r2.text[:400])
    except Exception as e:
        print(f'GET {path} -> ERR: {e}')
    sys.stdout.flush()

# Try fetching a JS bundle to find API routes
for script in scripts[:5]:
    if 'index' in script or 'app' in script or 'chunk' in script:
        url = base + script if script.startswith('/') else script
        try:
            r3 = s.get(url, timeout=10)
            content = r3.text
            # Find API paths
            api_paths = re.findall(r'["\`]/api/[a-zA-Z0-9/_?=&]{2,60}', content)
            for ap in set(api_paths):
                print(f'  API in JS: {ap}')
        except Exception as e:
            print(f'Script {script} -> ERR: {e}')
        break

# Try websocket or SSE endpoints
for path in ['/api/emails', '/api/inbox', '/api/message', '/api/check']:
    try:
        r4 = s.get(base + path + '?email=testclaude@kreabaka.site', timeout=8)
        print(f'GET {path}?email=... -> {r4.status_code} len={len(r4.text)}')
        if r4.status_code < 400:
            print(' ', r4.text[:400])
    except Exception as e:
        print(f'GET {path} -> ERR: {e}')
    sys.stdout.flush()
