#!/usr/bin/env python3
"""
unimail.py - UniMail CLI entry point.

Logic now lives in (split out for easier editing):
  cli_config.py    - config, ANSI helpers, cache I/O, email/domain parsing
  cli_tmq.py       - tempmailq.com client (sessions, CSRF, requests)
  cli_maildax.py   - maildax.cc client (placeholder)
  cli_commands.py  - all --flag command implementations

See cli_tmq.py for the CSRF protocol notes (HAR 2026-06-27).
"""

import sys
from cli_config import load_cache, err, c, set_debug
from cli_commands import (
    cmd_help, cmd_list_site, cmd_list_domain,
    cmd_mail_id, cmd_list_message, cmd_view_message, cmd_delete_id,
)


def main():
    args = sys.argv[1:]

    # --debug can appear anywhere in the args; strip it out and enable
    # debug logging before any command runs.
    if "--debug" in args:
        set_debug(True)
        args = [a for a in args if a != "--debug"]

    if not args:
        cmd_help()
        return

    cache = load_cache()
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ("-h", "--help"):
            cmd_help()

        elif arg == "--list-site":
            cmd_list_site()

        elif arg == "--list-domain":
            if i + 1 >= len(args): err("--list-domain requires a site name."); sys.exit(1)
            i += 1; cmd_list_domain(args[i])

        elif arg == "--mail-id":
            if i + 1 >= len(args): err("--mail-id requires user@domain."); sys.exit(1)
            i += 1; cmd_mail_id(args[i], cache)

        elif arg == "--list-message":
            if i + 1 >= len(args): err("--list-message requires user@domain."); sys.exit(1)
            i += 1; cmd_list_message(args[i], cache)

        elif arg == "--view-message":
            if i + 2 >= len(args): err("--view-message requires user@domain and a number."); sys.exit(1)
            i += 1; email_raw = args[i]
            i += 1
            try: serial = int(args[i])
            except ValueError: err(f"'{args[i]}' is not a valid number."); sys.exit(1)
            cmd_view_message(email_raw, serial, cache)

        elif arg == "--delete-id":
            if i + 1 >= len(args): err("--delete-id requires user@domain."); sys.exit(1)
            i += 1; cmd_delete_id(args[i], cache)

        else:
            err(f"Unknown argument: '{arg}'")
            print(f"  Run  {c('yellow','python unimail.py --help')}  for usage.")
            sys.exit(1)

        i += 1


if __name__ == "__main__":
    main()
