import json
from curl_cffi import requests as cr
from cli_config import load_cache, IMPERSONATE, HTTP_TIMEOUT
cache = load_cache()
mb = cache['mailboxes'].get('miaross21@tempforward.com', {})
token = mb.get('tempforward_token', '')
print('token prefix:', token[:20])

# Also try listing via inbox endpoint to see full fields
s = cr.Session(impersonate=IMPERSONATE)
s.headers.update({'Accept': 'application/json', 'Referer': 'https://tempforward.com/'})

# Check inbox first to see raw fields
inbox_url = 'https://tempforward.com/api/tempmail/inbox?token=' + token
r_inbox = s.get(inbox_url, timeout=HTTP_TIMEOUT)
print('inbox status:', r_inbox.status_code)
print('inbox data:', json.dumps(r_inbox.json(), indent=2))

# Now fetch specific message
msg_id = '534208'
url = 'https://tempforward.com/api/tempmail/email/' + msg_id + '?token=' + token
r = s.get(url, timeout=HTTP_TIMEOUT)
print('msg status:', r.status_code)
print('msg body:', json.dumps(r.json(), indent=2)[:3000])
