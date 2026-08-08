#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from cli_tempemail import tempemail_create_new, tempemail_list_messages
from cli_config import load_cache, set_debug

set_debug(True)
cache = load_cache()

print("Testing tempemail.cc...", flush=True)
try:
    s, addr = tempemail_create_new(cache)
    print(f"Created: {addr}", flush=True)
except Exception as e:
    print(f"Error creating: {e}", flush=True)
    sys.exit(1)

print("Listing messages...", flush=True)
try:
    msgs = tempemail_list_messages(addr, cache)
    print(f"Messages: {len(msgs)}", flush=True)
except Exception as e:
    print(f"Error listing: {e}", flush=True)

print("Done.", flush=True)
