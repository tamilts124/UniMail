#!/usr/bin/env python3
"""Quick test for tempmailo.com integration."""
import sys
import traceback
from cli_config import load_cache, save_cache

print("Loading cache...", flush=True)
cache = load_cache()

print("Importing tempmailo_com...", flush=True)
from cli_tempmailo_com import tempmailo_com_create_new, tempmailo_com_list_messages

print("Creating new address...", flush=True)
try:
    s, addr = tempmailo_com_create_new(cache)
    print(f"SUCCESS: address = {addr}", flush=True)
    
    print("Listing messages...", flush=True)
    msgs = tempmailo_com_list_messages(addr, cache)
    print(f"Messages: {len(msgs)} found", flush=True)
    
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print("DONE", flush=True)
