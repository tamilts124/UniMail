#!/usr/bin/env python3
"""Probe more services for viable APIs."""
from curl_cffi import requests as cr
import json

s = cr.Session(impersonate='chrome120')
s.headers.update({
    'Accept': 'application/json, application/ld+json',
    'Content-Type': 'application/json',
})

# Probe tmail.io more carefully
print('=== tmail.io ===')
for path in ['/', '/api/v1', '/api', '/inbox', '/mail']:
    try:
        r = s.get(f'https://tmail.io{path}', timeout=8)
        print(f'GET {path} -> {r.status_code} ({len(r.text)} bytes) ct={r.headers.get("content-type","?")}')
        if r.headers.get('content-type','').startswith('application/json') and r.status_code < 400:
            print('  ', r.text[:300])
    except Exception as e:
        print(f'GET {path} -> ERROR: {e}')

print()
print('=== mailcatch.com ===')
for path in ['/', '/api', '/api/v1', '/api/v1/inbox/testclaude', '/inbox/testclaude']:
    try:
        r = s.get(f'https://mailcatch.com{path}', timeout=8)
        print(f'GET {path} -> {r.status_code} ({len(r.text)} bytes) ct={r.headers.get("content-type","?")}')
        if r.status_code < 400 and r.headers.get('content-type','').startswith('application/json'):
            print('  ', r.text[:300])
    except Exception as e:
        print(f'GET {path} -> ERROR: {e}')

print()
print('=== moakt.com ===')
for path in ['/', '/api', '/api/v1', '/en/inbox']:
    try:
        r = s.get(f'https://www.moakt.com{path}', timeout=8)
        print(f'GET {path} -> {r.status_code} ({len(r.text)} bytes) ct={r.headers.get("content-type","?")}')
        if r.status_code < 400 and r.headers.get('content-type','').startswith('application/json'):
            print('  ', r.text[:300])
    except Exception as e:
        print(f'GET {path} -> ERROR: {e}')

print()
print('=== 10minemail.com ===')
for path in ['/', '/api', '/api/v1', '/email/new']:
    try:
        r = s.get(f'https://10minemail.com{path}', timeout=8)
        print(f'GET {path} -> {r.status_code} ({len(r.text)} bytes) ct={r.headers.get("content-type","?")}')
        if r.status_code < 400 and r.headers.get('content-type','').startswith('application/json'):
            print('  ', r.text[:300])
    except Exception as e:
        print(f'GET {path} -> ERROR: {e}')

print()
print('=== inboxes.com ===')
for path in ['/', '/api', '/api/v1/inbox/testclaude', '/inbox/testclaude']:
    try:
        r = s.get(f'https://inboxes.com{path}', timeout=8, headers={'Accept': 'application/json'})
        print(f'GET {path} -> {r.status_code} ({len(r.text)} bytes) ct={r.headers.get("content-type","?")}')
        if r.status_code < 400 and ('json' in r.headers.get('content-type','')):
            print('  ', r.text[:300])
    except Exception as e:
        print(f'GET {path} -> ERROR: {e}')
