import requests, json

candidates = [
    ('mail.gw', 'https://api.mail.gw/domains'),
    ('dispostable.com', 'https://dispostable.com/api/v1/inbox/testclaude'),
    ('mailnesia.com', 'https://mailnesia.com/mailbox/testclaude?format=atom'),
    ('spamspot.com', 'https://spamspot.com/mail/testclaude'),
    ('armyspy.com', 'https://www.armyspy.com/api/v1/inbox/testclaude'),
    ('rhyta.com', 'https://www.rhyta.com/api/v1/inbox/testclaude'),
    ('mail.td', 'https://mail.td/api/v2/mails?email=testclaude@mail.td'),
]

for name, url in candidates:
    try:
        r = requests.get(url, timeout=8, headers={'Accept': 'application/json, text/html'})
        ct = r.headers.get('content-type', '')
        if 'json' in ct:
            try:
                d = r.json()
                print(f'[{r.status_code}] {name}: JSON - {str(d)[:150]}')
            except:
                print(f'[{r.status_code}] {name}: JSON parse fail')
        else:
            print(f'[{r.status_code}] {name}: {ct[:50]} body={r.text[:100]}')
    except Exception as e:
        print(f'[ERR] {name}: {e}')
