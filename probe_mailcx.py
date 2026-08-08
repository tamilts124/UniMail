import requests, sys

# mail.cx - probe API endpoints
base = 'https://mail.cx'
headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

paths = [
    '/api/v1/inbox/testclaude25',
    '/api/inbox/testclaude25',
    '/api/v1/messages?inbox=testclaude25@mail.cx',
    '/api/messages/testclaude25',
    '/api/v1/mailbox/testclaude25',
]

for path in paths:
    try:
        r = requests.get(base + path, headers=headers, timeout=8)
        print(f"{path} => {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"{path} => ERR: {e}")

sys.stdout.flush()
