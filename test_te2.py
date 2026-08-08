import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from curl_cffi import requests as curl_requests
s = curl_requests.Session(impersonate='chrome124')
resp = s.get('https://www.tempemail.cc/api/domains', timeout=10)
print('Status:', resp.status_code, flush=True)
print('Body:', resp.text[:300], flush=True)
