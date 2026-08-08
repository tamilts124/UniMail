#!/usr/bin/env python3
"""Quick probe of mailinator.com public API."""
from curl_cffi import requests as rq
import json

s = rq.Session(impersonate='chrome124')
BASE = 'https://www.mailinator.com'
API  = 'https://api.mailinator.com'

# 1. Try public inbox fetch (no key)
inbox = 'testclaude2026'
domain = 'mailinator.com'
print('--- Test 1: public inbox API v2 (no key) ---')
r = s.get(f'{API}/v2/domains/{domain}/inboxes/{inbox}', timeout=15)
print('status:', r.status_code, '| body:', r.text[:300])

# 2. Try legacy GET msgs endpoint
print('--- Test 2: legacy /api/v2/inbox ---')
r2 = s.get(f'{API}/api/v2/inbox', params={'to': inbox}, timeout=15)
print('status:', r2.status_code, '| body:', r2.text[:300])

# 3. Try the website itself
print('--- Test 3: GET website homepage ---')
r3 = s.get(f'{BASE}/', timeout=15)
print('status:', r3.status_code, '| len:', len(r3.text))

# 4. Try mail_get endpoint used by the SPA
print('--- Test 4: GET /api/v2/message ---')
r4 = s.get(f'{BASE}/api/v2/message', params={'private_domain': 'false', 'domain': domain, 'to': inbox}, timeout=15)
print('status:', r4.status_code, '| body:', r4.text[:300])

print('DONE')
