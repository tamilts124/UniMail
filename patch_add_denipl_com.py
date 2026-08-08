#!/usr/bin/env python3
"""Add denipl.com to tempmailo.com domains in cli_config.py."""
import sys

PATH = r"D:\ClaudeDir\tempmail\cli_config.py"
with open(PATH, encoding="utf-8") as f:
    raw = f.read()
txt = raw.replace("\r\n", "\n")

if "denipl.com" in txt:
    print("Already present.")
    sys.exit(0)

OLD = '"tempmailo.com": ["denipl.net", "fxzig.com"],'
NEW = '"tempmailo.com": ["denipl.net", "denipl.com", "fxzig.com"],'
if OLD not in txt:
    print("ERROR: anchor not found!")
    sys.exit(1)
txt = txt.replace(OLD, NEW, 1)
out = txt.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(out)
print("Added denipl.com to tempmailo.com domain list.")
