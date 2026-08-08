#!/usr/bin/env python3
"""Probe third batch - inboxes.com, getnada.net, temp-mail.org, getnada.cc"""
import requests, json

results = {}
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def probe(name, method, url, **kwargs):
    try:
        r = getattr(S, method)(url, timeout=15, **kwargs)
        results[name] = {'status': r.status_code, 'ct': r.headers.get('content-type',''), 'body': r.text[:600]}
    except Exception as e:
        results[name] = {'error': str(e)}

# inboxes.com (getnada.com merged here)
probe('inboxes_domains', 'get', 'https://inboxes.com/api/v2/domains')
probe('inboxes_open', 'post', 'https://inboxes.com/api/v2/inbox/open', json={'email': 'testclaude@inboxes.com'})
probe('inboxes_root', 'get', 'https://inboxes.com/')

# getnada.net (new API)
probe('getnada_net_open', 'post', 'https://getnada.net/api/inbox/open', json={'email': 'testclaude@getnada.net'})
probe('getnada_net_domains', 'get', 'https://getnada.net/api/domains')

# getnada.cc (has embedded token API)
probe('getnada_cc_domains', 'get', 'https://getnada.cc/api/domains/GwNvKEofrdyS7JTXCzHQ')
probe('getnada_cc_msgs', 'get', 'https://getnada.cc/api/messages/testclaude@getnada.cc/GwNvKEofrdyS7JTXCzHQ')

# temp-mail.org - has public API (MD5 hash based)
import hashlib
email = 'testclaude@temp-mail.org'
email_hash = hashlib.md5(email.encode()).hexdigest()
probe('tempmail_org_msgs', 'get', f'https://api.temp-mail.org/request/mail/id/{email_hash}/format/json/')
probe('tempmail_org_domains', 'get', 'https://api.temp-mail.org/request/domains/format/json/')

# mailnesia - check for atom/rss
probe('mailnesia_atom', 'get', 'https://mailnesia.com/mailbox/testclaude?rss=1', headers={'Accept': 'application/atom+xml'})

# discard.email - check tempr.email API
probe('tempr_email_root', 'get', 'https://tempr.email/')
probe('tempr_email_json', 'get', 'https://tempr.email/com/checkmail.php', params={'username': 'testclaude', 'domain': 'discard.email'})

with open('probe3.json', 'w') as f:
    json.dump(results, f, indent=2)
print('probe3 complete')
