import urllib.request, json, ssl
ctx = ssl.create_default_context()

tests = [
    ('tempmailto.com /api/domains', 'GET', 'https://tempmailto.com/api/domains', None),
    ('tempmailto.com /api/v1/domains', 'GET', 'https://tempmailto.com/api/v1/domains', None),
    ('tempmailto.com /api/v1/mailbox/create', 'POST', 'https://tempmailto.com/api/v1/mailbox/create', b'{}'),
    ('temppostal.com /v1/emails', 'POST', 'https://api.temppostal.com/v1/emails', b'{}'),
    ('temp-mail.org domains', 'GET', 'https://temp-mail.org/en/api/v1/request/domains/format/json/', None),
    ('dispostable.com', 'GET', 'https://www.dispostable.com/api/inbox/?address=test@dispostable.com', None),
    ('mailnesia.com', 'GET', 'https://mailnesia.com/mailbox/test', None),
    ('mail.td', 'GET', 'https://mail.td/api/v1/inbox?address=test@mail.td', None),
    ('inboxes.com', 'GET', 'https://inboxes.com/api/v2/inbox/test', None),
]

for name, method, url, data in tests:
    try:
        req = urllib.request.Request(url, data=data, method=method,
            headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            body = r.read(200).decode('utf-8','ignore')
            print(f"[{r.status}] {name}: {body[:150]}")
    except Exception as e:
        print(f"[ERR] {name}: {str(e)[:100]}")
