#!/usr/bin/env python3
"""Session-4 tempmailo.com end-to-end test: create mailbox, print address, check inbox."""
import sys, os
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
os.chdir(r'D:\ClaudeDir\tempmail')

from cli_tempmailo_com import (
    _tempmailo_com_new_session, _fetch_token, _post_inbox,
    _generate_address, _tempmailo_com_pool, tempmailo_com_list_messages
)

cache = {"mailboxes": {}}

# Step 1: generate address and get token
address = _generate_address()
s       = _tempmailo_com_new_session()
token   = _fetch_token(s)

print(f"ADDRESS:{address}", flush=True)
print(f"TOKEN_OK:{bool(token)}", flush=True)

# Step 2: verify POST / works
resp = _post_inbox(s, token, address)
print(f"POST_STATUS:{resp.status_code}", flush=True)
if resp.status_code != 200:
    print(f"POST_BODY:{resp.text[:300]}", flush=True)
    sys.exit(1)

try:
    data = resp.json()
    print(f"JSON_OK:msgs={len(data) if isinstance(data, list) else data}", flush=True)
except Exception as e:
    print(f"JSON_ERR:{e} raw={resp.text[:200]}", flush=True)
    sys.exit(1)

# Register in pool so list_messages can use this session
_tempmailo_com_pool[address] = {"session": s, "token": token}
cache["mailboxes"][address] = {"tempmailo_com_token": token, "tempmailo_com_address": address}

print(f"READY", flush=True)
