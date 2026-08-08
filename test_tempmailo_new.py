#!/usr/bin/env python3
"""Test the new tempmailo_com implementation."""
import sys
from cli_config import load_cache
from cli_tempmailo_com import tempmailo_com_create_new, tempmailo_com_list_messages

print("Loading cache...", flush=True)
cache = load_cache()

print("Creating new mailbox...", flush=True)
try:
    s, addr = tempmailo_com_create_new(cache)
    print(f"SUCCESS: address = {addr}", flush=True)
    
    print("Listing messages...", flush=True)
    msgs = tempmailo_com_list_messages(addr, cache)
    print(f"Messages: {len(msgs)} found", flush=True)
    print(f"ADDRESS_FOR_TEST: {addr}", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback; traceback.print_exc()
    sys.exit(1)
print("DONE", flush=True)
