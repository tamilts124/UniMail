import json, subprocess, sys

# Step 1: clear old session
c = json.load(open(r'D:\ClaudeDir\tempmail\.unimail_cache.json'))
if 'testclaude@spymail.one' in c['mailboxes']:
    del c['mailboxes']['testclaude@spymail.one']
json.dump(c, open(r'D:\ClaudeDir\tempmail\.unimail_cache.json', 'w'), indent=2)
print('Old session cleared')

# Step 2: create new session
r = subprocess.run(['python', 'unimail.py', '--mail-id', 'testclaude@spymail.one'],
                   capture_output=True, text=True, cwd=r'D:\ClaudeDir\tempmail')
print('mail-id output:', r.stdout.strip()[:300])

# Step 3: get the assigned address
c2 = json.load(open(r'D:\ClaudeDir\tempmail\.unimail_cache.json'))
mb = c2['mailboxes'].get('testclaude@spymail.one', {})
addr = mb.get('dropmail_address', '')
print('Assigned address:', addr)
sys.stdout.flush()
