#!/usr/bin/env python3
"""Add the cli_tempmailo_com import to cli_commands.py."""
import sys

PATH = r"D:\ClaudeDir\tempmail\cli_commands.py"
with open(PATH, encoding="utf-8") as f:
    raw = f.read()
txt = raw.replace("\r\n", "\n")

if "cli_tempmailo_com" in txt:
    print("Import already present.")
    sys.exit(0)

ANCHOR = "from cli_tempforward import (\n    tempforward_create_new, tempforward_get_session, tempforward_list_messages,\n    tempforward_get_message, tempforward_delete_account,\n)"
ADD = "\nfrom cli_tempmailo_com import (\n    tempmailo_com_create_new, tempmailo_com_get_session, tempmailo_com_list_messages,\n    tempmailo_com_delete_account,\n)"

if ANCHOR not in txt:
    print("ERROR: anchor not found!")
    idx = txt.find("cli_tempforward")
    print(repr(txt[max(0,idx-10):idx+200]))
    sys.exit(1)

txt = txt.replace(ANCHOR, ANCHOR + ADD, 1)
out = txt.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(out)
print("Import added successfully.")
