#!/usr/bin/env python3
"""Poll tempmailo.com inbox 3 times with 10s gap"""
import sys, os, time
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
os.chdir(r'D:\ClaudeDir\tempmail')

from cli_tempmailo_com import _tempmailo_com_new_session, _fetch_token, _tempmailo_com_pool, tempmailo_com_list_messages

address = "znkghysyy@denipl.net"
cache = {"mailboxes": {address: {}}}

s = _tempmailo_com_new_session()
token = _fetch_token(s)
_tempmailo_com_pool[address] = {"session": s, "token": token}
cache["mailboxes"][address]["tempmailo_com_token"] = token
cache["mailboxes"][address]["tempmailo_com_address"] = address

for attempt in range(3):
    msgs = tempmailo_com_list_messages(address, cache)
    print(f"Attempt {attempt+1}: {len(msgs)} messages", flush=True)
    if msgs:
        for m in msgs:
            print(f"MAIL: from={m.get('from','?')} subj={m.get('subject','?')}", flush=True)
        print("PASS", flush=True)
        sys.exit(0)
    time.sleep(10)

print("NOT_YET", flush=True)
