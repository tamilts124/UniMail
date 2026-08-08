#!/usr/bin/env python3
"""Probe second batch of new temp mail services."""
import requests, json

results = {}
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def probe(name, method, url, **kwargs):
    try:
        r = getattr(S, method)(url, timeout=15, **kwargs)
        results[name] = {'status': r.status_code, 'ct': r.headers.get('content-type',''), 'body': r.text[:500]}
    except Exception as e:
        results[name] = {'error': str(e)}

# catchmail.io - try different endpoints
probe('catchmail_root', 'get', 'https://catchmail.io/')
probe('catchmail_api', 'get', 'https://catchmail.io/api/')
probe('catchmail_inbox', 'get', 'https://catchmail.io/api/inbox/testclaude')

# getnada - try different paths
probe('getnada_root', 'get', 'https://getnada.com/')
probe('getnada_api2', 'get', 'https://getnada.com/api/v1/domains')
probe('getnada_api3', 'get', 'https://getnada.com/api/v1/inbox/0/testclaude@nada.email')

# tempmail.io (different from temp-mail.io) - already in project
probe('tempmail_io_alt', 'get', 'https://api.tempmail.io/messages/testclaude@tempmail.io')

# inboxbear.com
probe('inboxbear', 'get', 'https://inboxbear.com/testclaude')

# mailtemp.info
probe('mailtemp_info', 'get', 'https://mailtemp.info/checkMail/?username=testclaude&domain=mailtemp.info')

# tempail.com (different)
probe('tempail_com', 'get', 'https://tempail.com/api/')

# spamgourmet.com - has an API
probe('spamgourmet', 'get', 'https://www.spamgourmet.com/jsonapi.pl?command=getmessages&email=testclaude.1.testme@spamgourmet.com')

# emailondeck.com API
probe('emailondeck', 'get', 'https://www.emailondeck.com/api/v2.0/get_email_address?site_token=test')

# minuteinbox
probe('minuteinbox_api', 'get', 'https://www.minuteinbox.com/index/index')

# yopmail - check if there's a JSON endpoint
probe('yopmail_json', 'get', 'https://yopmail.com/en/wm', params={'login': 'testclaude', 'p': '1', 'f': 'null', 'y': 'Y'})

with open('probe2.json', 'w') as f:
    json.dump(results, f, indent=2)
print('probe2 complete')
