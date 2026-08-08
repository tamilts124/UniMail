#!/usr/bin/env python3
from curl_cffi import requests as rq
import re

s = rq.Session(impersonate='chrome124')
r = s.get('https://www.mailinator.com/v4/public/js/m8rpublic.js', timeout=15)
js = r.text

# Find all HTTP/fetch/XHR URLs
print('=== URLs in JS ===')
urls = re.findall(r'["\x27](/(?:api|fetch|v[0-9]|inbox|msg|email|get)[^"\'\s]{0,100})', js)
for u in sorted(set(urls)):
    print(' ', u)

print('\n=== $http calls ===')
http_calls = re.findall(r'\$http\.(?:get|post)\([^)]{0,200}\)', js)
for c in http_calls[:20]:
    print(' ', c[:150])

print('\n=== fetch calls ===')
fetch_calls = re.findall(r'fetch\([^)]{0,200}\)', js)
for c in fetch_calls[:10]:
    print(' ', c[:150])

# Also look for the inbox data URL pattern
print('\n=== inbox/email patterns ===')
patterns = re.findall(r'["\x27][^"\x27]*(?:inbox|email|msg|fetch)[^"\x27]*["\x27]', js)
for p in sorted(set(patterns))[:20]:
    print(' ', p)

print('DONE')
