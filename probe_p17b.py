#!/usr/bin/env python3
"""Probe P17b services."""
from curl_cffi import requests as cr
import json

s = cr.Session(impersonate='chrome120')

def probe(name, url, method='GET', data=None, headers=None, timeout=10):
    try:
        h = {'Accept': 'application/json, */*'}
        if headers: h.update(headers)
        if method == 'GET':
            r = s.get(url, timeout=timeout, headers=h)
        else:
            r = s.post(url, json=data, timeout=timeout, headers=h)
        ct = r.headers.get('content-type','?')
        body = r.text[:400]
        print(f"  {name}: {r.status_code} ct={ct[:50]}")
        if r.status_code < 400:
            print(f"    body={body[:200]}")
        return r.status_code, ct, body
    except Exception as e:
        print(f"  {name}: ERROR {str(e)[:120]}")
        return 0, '', str(e)

# mailnesia.com — RSS-based (similar to eyepaste)
print('\n=== mailnesia.com ===')
probe('rss', 'https://mailnesia.com/mailbox/testclaude?rss')
probe('mailbox json', 'https://mailnesia.com/mailbox/testclaude', headers={'Accept': 'application/json'})
probe('api', 'https://mailnesia.com/api/mailbox/testclaude')

# tempemail.co (different from tempemail.cc)
print('\n=== tempemail.co ===')
probe('root', 'https://tempemail.co/')
probe('api generate', 'https://tempemail.co/api/generate')
probe('api inbox', 'https://tempemail.co/api/inbox/testclaude')
probe('api inbox2', 'https://tempemail.co/api/v1/inbox/testclaude')

# byom.de deeper probe
print('\n=== byom.de deeper ===')
probe('root', 'https://byom.de/')
probe('api/v1', 'https://byom.de/api/v1')
probe('mail list', 'https://byom.de/api/v1/mails/testclaude@byom.de')
probe('domains', 'https://byom.de/api/v1/domains')

# tempmail.cc (different from tempemail.cc in UniMail)
print('\n=== tempmail.cc ===')
probe('root', 'https://tempmail.cc/')
probe('api generate', 'https://tempmail.cc/api/generate')

# temporarymail.com
print('\n=== temporarymail.com ===')
probe('root', 'https://www.temporarymail.com/')
probe('api', 'https://www.temporarymail.com/api/v1')

# disposablemail.com
print('\n=== disposablemail.com ===')
probe('root', 'https://www.disposablemail.com/')
probe('api', 'https://www.disposablemail.com/api/inbox/testclaude')
probe('index', 'https://www.disposablemail.com/index/index')

# temp-inbox.com
print('\n=== temp-inbox.com ===')
probe('root', 'https://temp-inbox.com/')
probe('api', 'https://temp-inbox.com/api/inbox/testclaude')

print('\nDone.')
