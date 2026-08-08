import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from cli_config import load_cache, set_debug, HTTP_TIMEOUT
from cli_tempemail import tempemail_get_session
set_debug(True)
cache = load_cache()

s, token, acct_id = tempemail_get_session('naia2022@icmans.com', cache)
BASE = 'https://www.tempemail.cc/api'

# Try different body endpoints
msg_id = '204784071933431808'
endpoints = [
    f'/messages/{msg_id}/html',
    f'/messages/{msg_id}/source',
    f'/messages/{msg_id}/body',
    f'/messages/{msg_id}?type=html',
    f'/messages/{msg_id}?body=true',
]
for ep in endpoints:
    r = s.get(BASE + ep, headers={'Authorization': f'Bearer {token}'}, timeout=HTTP_TIMEOUT)
    print(f"GET {ep} -> {r.status_code}  {r.text[:200]}")
    print()
