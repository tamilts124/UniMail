#!/usr/bin/env python3
"""Probe new temp mail services to check their APIs."""
import requests, json

HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

def probe(name, url, **kw):
    try:
        r = requests.get(url, headers=HDR, timeout=15, **kw)
        ct = r.headers.get('content-type','')
        is_json = 'json' in ct or (r.text.strip().startswith('{') or r.text.strip().startswith('['))
        print(f"[{name}] {r.status_code} {ct[:40]} json={is_json}")
        print(f"  body: {r.text[:200]}")
    except Exception as e:
        print(f"[{name}] ERROR: {e}")

# mailnesia.com - try multiple endpoint formats
probe("mailnesia-api", "https://mailnesia.com/api/mailbox/testclaude5")
probe("mailnesia-rss", "https://mailnesia.com/mailbox/testclaude5.rss")

# getnada.net - documented REST API
probe("getnada-domains", "https://getnada.com/api/v1/domains")
probe("getnada-inbox", "https://getnada.com/api/v1/inboxes/0/testclaude5")

# catchmail.io
probe("catchmail-home", "https://catchmail.io/api/v1/inbox/testclaude5@catchmail.io")

# yopmail - check if there's a JSON API
probe("yopmail", "https://yopmail.com/en/inbox?login=testclaude5&p=&d=yopmail.com&ctrl=&yj=ZwZjZwHlAGZ4ZQHkZwN0Yw15ZmH5&yp=ZmZ4Zwt0ZGV3ZQH3ZGHl")

# mohmal.com - check for AJAX endpoints  
probe("mohmal-create", "https://www.mohmal.com/en/create")
probe("mohmal-inbox", "https://www.mohmal.com/en/inbox")

# temp-mail.org  
probe("tempmail-org", "https://api.temp-mail.org/request/mail/id/testclaude5md5/")

# minuteinbox.com
probe("minuteinbox", "https://minuteinbox.com/index/index")

# moakt.com
probe("moakt", "https://www.moakt.com/en/mail")

# trashmail.com
probe("trashmail", "https://trashmail.com/?cmd=get_messages&account=testclaude5&domain=trashmail.com&limit=10")

print("\nDone.")
import urllib.request, ssl
# NEW PROBE SESSION 11

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def probe(label, url, method='GET', data=None, headers=None):
    if headers is None:
        headers = {}
    try:
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header('User-Agent', 'Mozilla/5.0')
        for k, v in headers.items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            body = r.read(300).decode(errors='replace')
            print(f'{label}: HTTP {r.status} | {body[:200]}')
    except Exception as e:
        print(f'{label}: ERROR {str(e)[:150]}')

probe('dispostable', 'https://www.dispostable.com/api/v1/inbox/testclaude')
probe('mailnesia_rss', 'https://mailnesia.com/mailbox/testclaude?rss=1')
probe('altmails', 'https://altmails.com/api/inbox/testclaude')
probe('incognitomail', 'https://www.incognitomail.org/')
probe('spamspot_rss', 'http://www.spamspot.com/rss/testclaude')
probe('trbvm', 'http://trbvm.com/')
probe('armyspy', 'http://armyspy.com/')
probe('rhyta', 'http://rhyta.com/')
probe('einrot', 'http://einrot.com/')
probe('fleckens', 'http://fleckens.hu/')
probe('gustr', 'http://gustr.com/')
probe('mailismagic', 'http://mailismagic.com/')
probe('tempr_email', 'https://tempr.email/com/api/inbox/testclaude')
probe('cs_email', 'https://cs.email/api/inbox/testclaude')
probe('emailfake', 'https://emailfake.com/')
probe('easytrashmail', 'https://easytrashmail.com/')
