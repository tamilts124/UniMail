import json, sys
c = json.load(open(r'D:\ClaudeDir\tempmail\.unimail_cache.json'))
print(list(c['mailboxes'].keys())[:10])
for k, v in c['mailboxes'].items():
    if 'dropmail' in str(v):
        print('KEY:', k, 'VAL:', json.dumps(v)[:200])
