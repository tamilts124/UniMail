import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('cli_commands.py', encoding='utf-8') as f:
    txt = f.read()

# The duplicate header is because cmd_mail_id has two separate header() calls for fakemail.net
# Let's find and fix it
OLD = '''    if site == "fakemail.net":
        header(f"Mailbox: {email_key}")
        try:
            s, csrf = fakemail_get_session(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        real_addr = resolve_mock_id(email_key, cache)
        ok(f"Mailbox ready: {c('cyan', real_addr)}")
        info("Note", "Address is server-assigned (PHP session); use real address to receive mail")
        print()
        return'''

if OLD in txt:
    print("Found duplicate header block — already single header, no fix needed")
else:
    # Find what's in there around fakemail.net in cmd_mail_id
    idx = txt.find('site == "fakemail.net":\n        header')
    print(f"Found at index {idx}")
    print(repr(txt[idx:idx+400]))
