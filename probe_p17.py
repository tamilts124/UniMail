#!/usr/bin/env python3
"""Probe P17 services to find viable APIs."""
from curl_cffi import requests as cr
import json, time

s = cr.Session(impersonate='chrome120')
s.headers.update({'Accept': 'application/json, application/ld+json', 'Content-Type': 'application/json'})

def probe(name, url, method='GET', data=None, headers=None, timeout=10):
    try:
        h = {'Accept': 'application/json, application/ld+json', 'Content-Type': 'application/json'}
        if headers: h.update(headers)
        if method == 'GET':
            r = s.get(url, timeout=timeout, headers=h)
        else:
            if headers and 'x-www-form-urlencoded' in headers.get('Content-Type',''):
                r = s.post(url, data=data, timeout=timeout, headers=h)
            else:
                r = s.post(url, json=data, timeout=timeout, headers=h)
        ct = r.headers.get('content-type','?')
        body = r.text[:300]
        print(f"  {name}: {r.status_code} ct={ct[:40]}")
        if r.status_code < 400 and 'json' in ct:
            print(f"    body={body[:200]}")
        return r.status_code, ct, body
    except Exception as e:
        print(f"  {name}: ERROR {str(e)[:120]}")
        return 0, '', str(e)[:200]

# internxt.com temporary email (suspected mail.tm clone)
print('\n=== internxt.com/temporary-email ===')
probe('domains', 'https://api.internxt.com/api/v2/temp-email/domains')
probe('mailtm-style', 'https://internxt.com/api/temp-email/domains')

# tempail.com
print('\n=== tempail.com ===')
probe('root', 'https://tempail.com/')
probe('api request_email', 'https://tempail.com/api.php?lang=en-EN&method=request_email')
probe('api request_inbox', 'https://tempail.com/api.php?lang=en-EN&method=request_inbox_list')

# byom.de
print('\n=== byom.de ===')
probe('root', 'https://byom.de/')
probe('api mail GET', 'https://api.byom.de/mail/testclaude@byom.de')
probe('byom.de/en', 'https://byom.de/en')

# mintemail.com
print('\n=== mintemail.com ===')
probe('root', 'https://mintemail.com/')
probe('gea endpoint', 'https://mintemail.com/gea/', method='POST', data={'ee': 'testclaude@mintemail.com'})

# mail.td
print('\n=== mail.td ===')
probe('root', 'https://mail.td/')
probe('api.mail.td', 'https://api.mail.td/domains')

# tempmail.email
print('\n=== tempmail.email ===')
probe('domains', 'https://api.tempmail.email/domains')
probe('root', 'https://tempmail.email/')

# trashmail.de  
print('\n=== trashmail.de ===')
probe('root', 'https://trashmail.de/')
probe('api/v1', 'https://trashmail.de/api/v1/inbox/testclaude')
probe('check', 'https://trashmail.de/api/v1/check/testclaude')

# mailhole.de
print('\n=== mailhole.de ===')
probe('root', 'https://www.mailhole.de/')
probe('api inbox', 'https://www.mailhole.de/api/mailbox/testclaude')

# tempm.com
print('\n=== tempm.com ===')
probe('root', 'https://tempm.com/')
probe('api', 'https://tempm.com/api/')
probe('inbox', 'https://tempm.com/api/inbox/testclaude')

# mailper.com
print('\n=== mailper.com ===')
probe('root', 'https://www.mailper.com/')
probe('api', 'https://www.mailper.com/api/inbox/testclaude')

print('\nDone.')
