#!/usr/bin/env python3
import requests

endpoints = [
    ('GET', 'https://www.mohmal.com/api/new-email'),
    ('GET', 'https://www.mohmal.com/en/new-email'),
    ('POST', 'https://www.mohmal.com/en/create'),
    ('GET', 'https://www.mohmal.com/en/inbox/json'),
    ('GET', 'https://www.mohmal.com/api/inbox'),
    ('GET', 'https://www.mohmal.com/en/messages'),
]
hdrs = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://www.mohmal.com/en',
}
for method, url in endpoints:
    try:
        r = requests.request(method, url, headers=hdrs, timeout=12, allow_redirects=True)
        print(f"{method} {url} -> {r.status_code} | {r.text[:120]}")
    except Exception as e:
        print(f"{method} {url} -> ERROR: {e}")
print("done")
