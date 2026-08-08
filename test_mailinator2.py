#!/usr/bin/env python3
"""Probe mailinator SPA API endpoints used by the browser."""
from curl_cffi import requests as rq
import re

s = rq.Session(impersonate='chrome124')
BASE = 'https://www.mailinator.com'

# Fetch homepage to see what JS APIs it calls
r = s.get(f'{BASE}/', timeout=15)
html = r.text

# Find API references in the HTML/JS
api_refs = re.findall(r'[\'"](/(?:api|v[0-9])[^\'"]{0,80})[\'"]', html)
print('API refs found in HTML:', set(api_refs))

# Try the actual inbox URL the SPA uses
inbox = 'testclaude2026'
domain = 'mailinator.com'

# Try routes the website itself uses
for path in [
    f'/api/v2/domains/{domain}/inboxes/{inbox}?skip=0&limit=50&sort=newest&decode_subject=true',
    f'/api/v2/message/mailinator/{inbox}',
    f'/fetch_email?msgid={inbox}',
    f'/email/{inbox}',
]:
    r2 = s.get(BASE + path, timeout=10)
    print(f'  {path[:60]}: {r2.status_code} | {r2.text[:150]}')

print('DONE')
