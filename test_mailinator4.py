#!/usr/bin/env python3
"""Probe mailinator inbox API after sending a test email."""
from curl_cffi import requests as rq
import json, time

s = rq.Session(impersonate='chrome124')
BASE = 'https://www.mailinator.com'
inbox = 'testclaude2026'

# The AngularJS SPA calls these endpoints — probe them directly
endpoints = [
    f'/api/v2/domains/mailinator.com/inboxes/{inbox}',
    f'/api/v2/domains/mailinator/inboxes/{inbox}',
    f'/api/v2/inboxes/{inbox}',
    f'/api/v2/message/{inbox}',
    '/api/v2/inbox',
]

for path in endpoints:
    params = {'to': inbox} if 'inbox' not in path or path.endswith('/inbox') else {}
    try:
        r = s.get(BASE + path, params=params, timeout=10)
        print(f'{path[:60]}: {r.status_code} | {r.text[:200]}')
    except Exception as e:
        print(f'{path[:60]}: ERROR {e}')

# Try with the Referer header set
print('\n--- with Referer header ---')
s.headers['Referer'] = f'{BASE}/v4/public/inboxes.jsp?to={inbox}'
s.headers['X-Requested-With'] = 'XMLHttpRequest'
for path in ['/api/v2/domains/mailinator.com/inboxes/' + inbox,
             f'/api/v2/message/{inbox}@mailinator.com']:
    r = s.get(BASE + path, timeout=10)
    print(f'{path[:60]}: {r.status_code} | {r.text[:200]}')

print('DONE')
