#!/usr/bin/env python3
"""Quick test for tempmailo.com - run from D:\ClaudeDir\tempmail"""
import sys, os
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
os.chdir(r'D:\ClaudeDir\tempmail')

print("STARTING tempmailo.com test", flush=True)
try:
    from cli_tempmailo_com import tempmailo_com_create_new, tempmailo_com_list_messages
    print("IMPORT OK", flush=True)
    cache = {"mailboxes": {}}
    s, address = tempmailo_com_create_new(cache)
    print(f"ADDRESS: {address}", flush=True)
    msgs = tempmailo_com_list_messages(address, cache)
    print(f"INBOX OK: {len(msgs)} messages", flush=True)
    print("RESULT: PASS", flush=True)
except Exception as e:
    import traceback
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
    print("RESULT: FAIL", flush=True)
