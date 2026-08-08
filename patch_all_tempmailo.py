#!/usr/bin/env python3
"""
One-shot patch: add tempmailo.com dispatch to all 4 cmd_* functions.
Run once on a clean cli_commands.py (no prior tempmailo patches).
"""
import sys, re

PATH = r"D:\ClaudeDir\tempmail\cli_commands.py"
with open(PATH, encoding="utf-8") as f:
    raw = f.read()

txt = raw.replace("\r\n", "\n")

if 'site == "tempmailo.com"' in txt:
    print("Already patched - aborting.")
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: insert BLOCK just before the first occurrence of ANCHOR
# ─────────────────────────────────────────────────────────────────────────────
def insert_before(text, anchor, block, label):
    idx = text.find(anchor)
    if idx == -1:
        print(f"ERROR [{label}]: anchor not found:\n{anchor[:120]!r}")
        sys.exit(1)
    return text[:idx] + block + "\n" + text[idx:]

# ═══════════════════════════════════════════════════════════════════════════ 1
# cmd_mail_id — insert before the LARAVEL guard
# ═══════════════════════════════════════════════════════════════════════════ 1
ANCHOR1 = '    if site not in LARAVEL_SITES:\n        err(f"cmd_mail_id for {site} not yet implemented.")'

BLOCK1 = '''\
    if site == "tempmailo.com":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("tempmailo_com_token") and mb.get("tempmailo_com_address"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                s, token = tempmailo_com_get_session(email_key, cache)
                real_addr = mb.get("tempmailo_com_address", email_key)
                ok("Session restored from cache.")
                info("Email", real_addr)
                info("Token", token[:20] + "...")
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache - creating new tempmailo.com inbox ...")
        try:
            s, address = tempmailo_com_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', address)}")
        info("Note", "Address is server-assigned (ASP.NET + Cloudflare)")
        if address != email_key:
            cache["mailboxes"].setdefault(email_key, {})["redirect_to"] = address
            save_cache(cache)
            info("Redirect", f"{email_key} -> {address}")
        print()
        return
'''
txt = insert_before(txt, ANCHOR1, BLOCK1, "cmd_mail_id")
print("Patch 1 done (cmd_mail_id).")

# ═══════════════════════════════════════════════════════════════════════════ 2
# cmd_list_message — insert before the first LARAVEL guard for list_message
# ═══════════════════════════════════════════════════════════════════════════ 2
ANCHOR2 = '    if site not in LARAVEL_SITES:\n        err(f"cmd_list_message for {site} not yet implemented.")'

BLOCK2 = '''\
    if site == "tempmailo.com":
        header(f"Messages in {email_key}")
        try:
            msgs = tempmailo_com_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        # fields: id, from, subject, date, text, html
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("date", ""),
                "is_read":    False,
                "body_html":  m.get("html", ""),
                "body_plain": m.get("text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "\t") if msg.get("is_read") else c("yellow", "?")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return
'''
txt = insert_before(txt, ANCHOR2, BLOCK2, "cmd_list_message")
print("Patch 2 done (cmd_list_message).")

# ═══════════════════════════════════════════════════════════════════════════ 3
# cmd_view_message — insert before the bare err() fallthrough
# ═══════════════════════════════════════════════════════════════════════════ 3
ANCHOR3 = '        err(f"cmd_view_message for {site} not yet implemented.")\n        sys.exit(1)'

BLOCK3 = '''\
    if site == "tempmailo.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        header(f"Message #{serial}  -  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "-"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return
'''
txt = insert_before(txt, ANCHOR3, BLOCK3, "cmd_view_message")
print("Patch 3 done (cmd_view_message).")

# ═══════════════════════════════════════════════════════════════════════════ 4
# cmd_delete_id — insert before the LARAVEL guard
# ═══════════════════════════════════════════════════════════════════════════ 4
ANCHOR4 = '    if site not in LARAVEL_SITES:\n        err(f"cmd_delete_id for {site} not yet implemented.")'

BLOCK4 = '''\
    if site == "tempmailo.com":
        header(f"Delete: {email_key}")
        tempmailo_com_delete_account(email_key, cache)
        ok(f"Removed '{email_key}' from local cache (no server-side delete endpoint).")
        print()
        return
'''
txt = insert_before(txt, ANCHOR4, BLOCK4, "cmd_delete_id")
print("Patch 4 done (cmd_delete_id).")

# ─────────────────────────────────────────────────────────────────────────────
# Write back (CRLF for Windows)
# ─────────────────────────────────────────────────────────────────────────────
out = txt.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(out)

total = txt.count('site == "tempmailo.com"')
print(f"\nAll done. {total} tempmailo.com blocks in cli_commands.py.")
