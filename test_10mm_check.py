#!/usr/bin/env python3
# Check if 10minutemail session still alive and if test email arrived
from curl_cffi import requests as rq
from cli_config import load_cache
import json

# Create fresh session and send test email to it
s = rq.Session(impersonate='chrome124')
print('Creating new 10mm session...')
resp = s.get('https://10minutemail.com/', timeout=20)
addr_resp = s.get('https://10minutemail.com/session/address', timeout=15)
addr = addr_resp.json()['address']
print('Assigned address:', addr)
print('Now check for messages...')
msgs = s.get('https://10minutemail.com/messages/messagesAfter/0', timeout=15).json()
print(f'Messages: {len(msgs)}')
for m in msgs:
    print(f'  Subject: {m.get("subject")} | From: {m.get("sender")}')
print('DONE')
