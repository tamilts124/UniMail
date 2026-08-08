#!/usr/bin/env python3
"""Create a fresh tempmailo.com address and print it."""
import sys
sys.path.insert(0, r'D:\ClaudeDir\tempmail')
from cli_config import load_cache, save_cache
from cli_tempmailo_com import tempmailo_com_create_new

cache = load_cache()
s, address = tempmailo_com_create_new(cache)
print(f"ADDRESS:{address}")
