#!/usr/bin/env python3
"""Probe P17c services - tmail.delivery, mailscr.us, tmailor.com, m.kuku.lu, burnermail.io."""
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
        body = r.text[:300]
        print(f"  {name}: {r.status_code} ct={ct[:50]}")
        if r.status_code < 400 and 'json' in ct:
            print(f"    body={body[:200]}")
        elif r.status_code < 400:
            print(f"    body(html)={body[:80]}")
        return r.status_code, ct, body
    except Exception as e:
        print(f"  {name}: ERROR {str(e)[:120]}")
        return 0, '', str(e)

# tmail.delivery — 105 domains, worth probing
print('\n=== tmail.delivery ===')
probe('root', 'https://tmail.delivery/')
probe('api', 'https://tmail.delivery/api/')
probe('domains', 'https://tmail.delivery/api/v1/domains')
probe('inbox', 'https://tmail.delivery/api/v1/inbox/testclaude')
probe('email', 'https://tmail.delivery/api/v1/email/testclaude@tmail.delivery')

# mailscr.us — 102 domains
print('\n=== mailscr.us ===')
probe('root', 'https://mailscr.us/')
probe('api', 'https://mailscr.us/api/')
probe('inbox', 'https://mailscr.us/api/inbox/testclaude')

# m.kuku.lu
print('\n=== m.kuku.lu ===')
probe('root', 'https://m.kuku.lu/')
probe('api', 'https://m.kuku.lu/api/v1')
probe('inbox', 'https://m.kuku.lu/api/v1/inbox/testclaude@kuku.lu')

# tmailor.com
print('\n=== tmailor.com ===')
probe('root', 'https://tmailor.com/')
probe('api v1', 'https://tmailor.com/api/v1')
probe('domains', 'https://tmailor.com/api/v1/domains')

# burnermail.io
print('\n=== burnermail.io ===')
probe('root', 'https://burnermail.io/')
probe('api', 'https://burnermail.io/api/')
probe('inbox', 'https://burnermail.io/api/v1/inbox/testclaude')

# trashmailr.com
print('\n=== trashmailr.com ===')
probe('root', 'https://trashmailr.com/')
probe('api', 'https://trashmailr.com/api/')

# mail-temp.site
print('\n=== mail-temp.site ===')
probe('root', 'https://mail-temp.site/')
probe('api', 'https://mail-temp.site/api/')
probe('inbox', 'https://mail-temp.site/api/inbox/testclaude')

# tmail.io - try more paths
print('\n=== tmail.io extra paths ===')
probe('email new', 'https://tmail.io/v1/email/new', method='POST', data={})
probe('email get', 'https://tmail.io/v1/email/testclaude@tmail.io')
probe('messages', 'https://tmail.io/v1/messages/testclaude@tmail.io')

print('\nDone.')
