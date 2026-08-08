#!/usr/bin/env python3
"""Check inbox for qkazqq@denipl.net"""
import sys, os
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
os.chdir(r'D:\ClaudeDir\tempmail')

from cli_tempmailo_com import (
    _tempmailo_com_new_session, _fetch_token, _post_inbox, _tempmailo_com_pool,
    tempmailo_com_list_messages
)

address = "qkazqq@denipl.net"
s     = _tempmailo_com_new_session()
token = _fetch_token(s)
_tempmailo_com_pool[address] = {"session": s, "token": token}
cache = {"mailboxes": {address: {"tempmailo_com_token": token, "tempmailo_com_address": address}}}

msgs = tempmailo_com_list_messages(address, cache)
print(f"COUNT:{len(msgs)}", flush=True)
for m in msgs:
    print(f"FROM:{m.get('from','?')} SUBJ:{m.get('subject','?')}", flush=True)
if msgs:
    print("RESULT:PASS", flush=True)
else:
    print("RESULT:EMPTY", flush=True)
