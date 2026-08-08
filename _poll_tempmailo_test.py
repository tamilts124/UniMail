#!/usr/bin/env python3
"""Poll tempmailo.com inbox for test email - waits up to 90s"""
import sys, os, time
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
os.chdir(r'D:\ClaudeDir\tempmail')

from cli_tempmailo_com import tempmailo_com_create_new, tempmailo_com_list_messages

address = "znkghysyy@denipl.net"
cache = {"mailboxes": {address: {}}}

# Create session for existing address
from cli_tempmailo_com import _tempmailo_com_new_session, _fetch_token, _tempmailo_com_pool
s = _tempmailo_com_new_session()
token = _fetch_token(s)
_tempmailo_com_pool[address] = {"session": s, "token": token}
cache["mailboxes"][address]["tempmailo_com_token"] = token
cache["mailboxes"][address]["tempmailo_com_address"] = address

print(f"Polling inbox for {address} ...", flush=True)
for attempt in range(6):
    msgs = tempmailo_com_list_messages(address, cache)
    print(f"  Attempt {attempt+1}: {len(msgs)} messages", flush=True)
    if msgs:
        for m in msgs:
            print(f"  MAIL: from={m.get('from','?')} subject={m.get('subject','?')}", flush=True)
        print("RESULT: PASS - email received!", flush=True)
        sys.exit(0)
    if attempt < 5:
        time.sleep(15)

print("RESULT: FAIL - no email after 90s", flush=True)
sys.exit(1)
