#!/usr/bin/env python3
from curl_cffi import requests as curl_requests
import json

s = curl_requests.Session(impersonate='chrome124')
s.headers['Accept'] = 'application/json'
s.headers['Origin'] = 'https://openinbox.io'
s.headers['Referer'] = 'https://openinbox.io/'

print("Testing POST /api/inbox ...")
r = s.post('https://api.openinbox.io/api/inbox', json={}, timeout=15)
print(f"STATUS: {r.status_code}")
print(f"BODY: {r.text[:400]}")

if r.status_code in (200, 201):
    data = r.json()
    inbox_id = data.get('id')
    email = data.get('email')
    print(f"\nCreated: {email} (id={inbox_id})")
    
    print(f"\nTesting GET /api/inbox/{inbox_id}/emails ...")
    r2 = s.get(f'https://api.openinbox.io/api/inbox/{inbox_id}/emails', timeout=15)
    print(f"STATUS: {r2.status_code}")
    print(f"BODY: {r2.text[:200]}")
