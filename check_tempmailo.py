#!/usr/bin/env python3
"""Directly test the tempmailo.com POST / endpoint."""
import sys
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
from cli_config import load_cache
from cli_tempmailo_com import tempmailo_com_list_messages, tempmailo_com_create_new

cache = load_cache()

# Check pkldcgg@denipl.com  
address = "pkldcgg@denipl.com"
print(f"Checking inbox: {address}")
try:
    msgs = tempmailo_com_list_messages(address, cache)
    print(f"Messages: {len(msgs)}")
    for m in msgs:
        print(f"  Subject: {m.get('subject','?')} | From: {m.get('from','?')}")
except Exception as e:
    print(f"Error: {e}")

# Also check the previous fxzig one from cache
print("\nChecking old address: iyjbggjntu@fxzig.com")
try:
    msgs2 = tempmailo_com_list_messages("iyjbggjntu@fxzig.com", cache)
    print(f"Messages: {len(msgs2)}")
    for m in msgs2:
        print(f"  Subject: {m.get('subject','?')} | From: {m.get('from','?')}")
except Exception as e:
    print(f"Error: {e}")
