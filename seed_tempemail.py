import json

with open('.unimail_cache.json') as f:
    cache = json.load(f)

cache['mailboxes']['naia2022@icmans.com'] = {
    'tempemail_token': 'eyJhbGciOiJFZERTQSJ9.eyJpYXQiOjE3ODQ0NzU1MzgsImlkIjoiMjA0NzQyMzMwMjE1ODI5NTA0Iiwib3duZXJJZCI6IjIwNDc0MjMzMDIxNTgyOTUwNCIsIm1haWxib3hUeXBlIjowLCJtZXJjdXJlIjp7InN1YnNjcmliZSI6WyIvdS8yMDQ3NDIzMzAyMTU4Mjk1MDQiXX19.UuuYb4jaRUJ-X-XA_vBtm_lknnO3GxN3KoPIvRGWS0HWjodgqIqBJ6dF4Dej3VPxUrscCZHNJxZ30W5DG4SiAw',
    'tempemail_account_id': '204742330215829504',
    'tempemail_password': 'PpJ*h8wGl9'
}

with open('.unimail_cache.json', 'w') as f:
    json.dump(cache, f, indent=2)

print('SUCCESS: seeded naia2022@icmans.com into cache')

# Verify
with open('.unimail_cache.json') as f:
    cache2 = json.load(f)
mb = cache2['mailboxes'].get('naia2022@icmans.com', {})
print('VERIFY token:', mb.get('tempemail_token', 'MISSING')[:40])
