#!/usr/bin/env python3
"""Probe new temp mail services for API availability."""
import requests, json, sys

results = {}
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def probe(name, method, url, **kwargs):
    try:
        r = getattr(S, method)(url, timeout=15, **kwargs)
        results[name] = {'status': r.status_code, 'ct': r.headers.get('content-type',''), 'body': r.text[:400]}
    except Exception as e:
        results[name] = {'error': str(e)}

# tempmail.lol - v2 API
probe('tempmail_lol_create', 'post', 'https://api.tempmail.lol/v2/inbox/create')

# getnada.com
probe('getnada_inbox', 'get', 'https://getnada.com/api/v1/inboxes/testclaude')

# catchmail.io
probe('catchmail_io', 'get', 'https://catchmail.io/api/messages/testclaude@catchmail.io')

# mohmal.com - check for JSON API
probe('mohmal_json', 'get', 'https://www.mohmal.com/api/inbox/testclaude')
probe('mohmal_page', 'get', 'https://www.mohmal.com/en/inbox/testclaude')

# discard.email
probe('discard_email', 'get', 'https://discard.email/mailbox/testclaude')

# mailnesia.com
probe('mailnesia_rss', 'get', 'https://mailnesia.com/mailbox/testclaude?rss=1')

# trashmail.com
probe('trashmail_get', 'get', 'https://trashmail.com/?cmd=get_messages&account=testclaude')

# dispostable.com
probe('dispostable', 'get', 'https://www.dispostable.com/api/inbox/', params={'recipient': 'testclaude', 'domain': 'dispostable.com'})

# Write results
with open('probe_new_services.json', 'w') as f:
    json.dump(results, f, indent=2)
print('probe complete')
