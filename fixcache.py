import json

c = json.load(open(r'D:\ClaudeDir\tempmail\.unimail_cache.json'))
# Remove the chained dropmail entries - keep only testclaude@spymail.one
keys_to_del = []
for k in list(c['mailboxes'].keys()):
    v = c['mailboxes'][k]
    if isinstance(v, dict) and 'dropmail' in str(v) and k != 'testclaude@spymail.one':
        keys_to_del.append(k)
        print('Removing:', k)

# Also clean up testclaude@spymail.one - remove redirect_to, keep valid session
mb = c['mailboxes'].get('testclaude@spymail.one', {})
if 'redirect_to' in mb:
    del mb['redirect_to']
    print('Removed redirect_to from testclaude@spymail.one')

for k in keys_to_del:
    del c['mailboxes'][k]

json.dump(c, open(r'D:\ClaudeDir\tempmail\.unimail_cache.json', 'w'), indent=2)
print('Cache cleaned. testclaude@spymail.one session:', mb.get('dropmail_address'))
