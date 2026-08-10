#!/usr/bin/env python3
"""Deep probe of mailscr.us which has a working /api/domains endpoint."""
from curl_cffi import requests as cr
import json, sys

s = cr.Session(impersonate='chrome120')
s.headers.update({'Accept': 'application/json, */*', 'Content-Type': 'application/json'})

def p(label, url, method='GET', data=None):
    try:
        r = s.request(method, url, json=data, timeout=10)
        ct = r.headers.get('content-type','?')
        print(f'{method} {label} -> {r.status_code} ct={ct[:60]} len={len(r.text)}')
        if r.text.strip():
            print('  ', r.text[:600])
    except Exception as e:
        print(f'{method} {label} -> ERR: {e}')
    sys.stdout.flush()

base = 'https://mailscr.us'

# First get domains list 
p('/api/domains', base + '/api/domains')

# Try to get inbox / messages
p('/api/messages', base + '/api/messages')
p('/api/inbox/testclaude', base + '/api/inbox/testclaude')
p('/api/inbox/testclaude@kreabaka.site', base + '/api/inbox/testclaude@kreabaka.site')
p('/api/v1/inbox', base + '/api/v1/inbox')
p('/api/email/new', base + '/api/email/new', 'POST', {})
p('/api/email/new GET', base + '/api/email/new')
p('/api/generate', base + '/api/generate')
p('/api/create', base + '/api/create', 'POST', {'domain': 'kreabaka.site'})
p('/api/mailbox', base + '/api/mailbox')
p('/api/mailbox GET', base + '/api/mailbox?email=testclaude@kreabaka.site')
p('/api/token', base + '/api/token', 'POST', {})

# What does the HTML page look like?
r = s.get(base + '/', timeout=10)
print('\n=== HTML page snippets ===')
html = r.text
# Look for API calls in scripts
import re
scripts = re.findall(r'(fetch|axios|xhr|api)\s*[(`\'"]([^`\'"]{3,80})', html, re.I)
for s_tag in scripts[:30]:
    print(f'  Script ref: {s_tag}')
# Look for any /api/ references
api_refs = re.findall(r'/api/[^\s\'"<>]{2,60}', html)
for ref in set(api_refs):
    print(f'  API ref: {ref}')
