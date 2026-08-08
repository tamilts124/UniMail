#!/usr/bin/env python3
from curl_cffi import requests as rq
import sys
s = rq.Session(impersonate='chrome124')
print('Getting 10minutemail homepage...', flush=True)
r = s.get('https://10minutemail.com/', timeout=20)
print('status:', r.status_code, flush=True)
r2 = s.get('https://10minutemail.com/session/address', timeout=15)
print('address:', r2.json(), flush=True)
msgs = s.get('https://10minutemail.com/messages/messagesAfter/0', timeout=15).json()
print('messages:', len(msgs), flush=True)
for m in msgs:
    print(' -', m.get('subject'), 'from:', m.get('sender'), flush=True)
print('DONE', flush=True)
