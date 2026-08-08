import json
from curl_cffi import requests as cr

r = cr.get('https://48hr.email/api/inbox/testclaude', timeout=10, impersonate='chrome124')
data = r.json()
open('probe23_out.txt','w',encoding='utf-8').write(json.dumps(data, indent=2))
print("count:", data.get('count',0))
if data.get('data'):
    msg = data['data'][0]
    print("keys:", list(msg.keys()))
    msg_id = msg.get('id') or msg.get('messageId') or msg.get('_id') or ''
    print("id:", msg_id)
    for path in [f'/api/inbox/testclaude/{msg_id}', f'/api/message/{msg_id}']:
        r2 = cr.get(f'https://48hr.email{path}', timeout=8, impersonate='chrome124')
        open('probe23_out.txt','a',encoding='utf-8').write(f"\n---{path}---\n{r2.status_code}:{r2.text[:600]}")
        print(path, r2.status_code, r2.text[:100])
