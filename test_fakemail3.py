import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('.unimail_cache.json', encoding='utf-8') as f:
    cache = json.load(f)

for k, v in cache.get('mailboxes', {}).items():
    if 'fakemail' in str(v) or 'forliion' in k:
        print(f"{k!r}: {v!r}")
