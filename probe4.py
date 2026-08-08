#!/usr/bin/env python3
"""Deep probe of getnada.net API."""
import requests, json

results = {}
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def probe(name, method, url, **kwargs):
    try:
        r = getattr(S, method)(url, timeout=15, **kwargs)
        results[name] = {'status': r.status_code, 'ct': r.headers.get('content-type',''), 'body': r.text[:800]}
    except Exception as e:
        results[name] = {'error': str(e)}

# Step 1: Open/create inbox at getnada.net
r = S.post('https://getnada.net/api/inbox/open', json={'email': 'testclaude2@getnada.net'}, timeout=15)
results['getnada_net_open'] = {'status': r.status_code, 'body': r.text[:800]}

if r.status_code == 200:
    data = r.json()
    token = data.get('token', '')
    inbox_id = data.get('inboxId', '')
    
    # Step 2: List messages using token
    probe('getnada_net_messages', 'get', f'https://getnada.net/api/inbox/{inbox_id}/messages',
          headers={'Authorization': f'Bearer {token}'})
    
    # Step 3: Try to get domains
    probe('getnada_net_domains', 'get', 'https://getnada.net/api/domains',
          headers={'Authorization': f'Bearer {token}'})
    
    # Step 4: Try messages without auth
    probe('getnada_net_msgs_noauth', 'get', f'https://getnada.net/api/inbox/{inbox_id}/messages')
    
    # Step 5: Try different message listing paths
    probe('getnada_net_msgs2', 'get', f'https://getnada.net/api/messages/{inbox_id}',
          headers={'Authorization': f'Bearer {token}'})
    
    # Store token for reference
    results['token_saved'] = {'token': token[:50] + '...', 'inbox_id': inbox_id, 'recipient': data.get('recipient',''), 'activeUntil': data.get('activeUntil','')}

with open('probe4.json', 'w') as f:
    json.dump(results, f, indent=2)
print('probe4 complete')
