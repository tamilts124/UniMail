#!/usr/bin/env python3
"""Probe mail.gw API endpoints."""
from curl_cffi import requests as cr
import json

s = cr.Session(impersonate='chrome120')
s.headers.update({
    'Accept': 'application/json, application/ld+json',
    'Content-Type': 'application/json',
})

print('=== Probing api.mail.gw ===')
try:
    r = s.get('https://api.mail.gw/domains', timeout=15)
    print(f'GET /domains -> {r.status_code}')
    print(r.text[:1000])
except Exception as e:
    print(f'ERROR: {e}')

print()
print('=== Probe more PENDING services ===')

services = [
    ('tmail.io', 'https://tmail.io'),
    ('tmpmail.co', 'https://tmpmail.co'),
    ('temp.cab', 'https://temp.cab'),
    ('mailcatch.com', 'https://mailcatch.com'),
    ('mytemp.email', 'https://mytemp.email'),
    ('moakt.com', 'https://www.moakt.com'),
    ('10minemail.com', 'https://10minemail.com'),
    ('inboxes.com', 'https://inboxes.com'),
]

for name, url in services:
    try:
        r2 = s.get(url + '/api', timeout=8)
        print(f'{name} /api -> {r2.status_code} ({len(r2.text)} bytes)')
    except Exception as e:
        print(f'{name} -> ERROR: {e}')
