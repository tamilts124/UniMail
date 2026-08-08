#!/usr/bin/env python3
"""Probe mailinator v4 public JSP API."""
from curl_cffi import requests as rq

s = rq.Session(impersonate='chrome124')
BASE = 'https://www.mailinator.com'
inbox = 'testclaude2026'

# Try the v4 public inboxes endpoint
for path in [
    f'/v4/public/inboxes.jsp?to={inbox}',
    f'/v4/public/inboxes.jsp?to={inbox}&domain=mailinator.com',
    f'/v4/public/inboxes.jsp?to={inbox}@mailinator.com',
    f'/v4/public/msgid/{inbox}',
    f'/v4/public/inboxes.jsp?to={inbox}&zone=public',
]:
    r = s.get(BASE + path, timeout=10)
    print(f'{path[:70]}: {r.status_code} | {r.text[:200]}')
    print()

# Also check the fetch_email endpoint more carefully with zone
for zone in ['public', 'mailinator', 'private']:
    r2 = s.get(f'{BASE}/fetch_email?msgid={inbox}&zone={zone}', timeout=10)
    print(f'fetch_email zone={zone}: {r2.status_code} | {r2.text[:200]}')

print('DONE')
