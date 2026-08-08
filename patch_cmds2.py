import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('cli_commands.py', encoding='utf-8') as f:
    txt = f.read()

# Remove the duplicate header() call in the fakemail.net branch of cmd_mail_id
OLD = '    if site == "fakemail.net":\n        header(f"Mailbox: {email_key}")\n        try:\n            s, csrf = fakemail_get_session(email_key, cache)'
NEW = '    if site == "fakemail.net":\n        try:\n            s, csrf = fakemail_get_session(email_key, cache)'

if OLD in txt:
    txt2 = txt.replace(OLD, NEW, 1)
    with open('cli_commands.py', 'w', encoding='utf-8') as f:
        f.write(txt2)
    print("Patched: removed duplicate header() from fakemail.net branch")
else:
    print("Pattern not found!")
    idx = txt.find('site == "fakemail.net":\n        header')
    print(repr(txt[idx:idx+300]))
