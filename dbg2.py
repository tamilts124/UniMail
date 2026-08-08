import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open('cli_commands.py', encoding='utf-8') as f:
    txt = f.read()
# find cmd_mail_id start
idx = txt.find('def cmd_mail_id(')
# print first 300 chars of function
print(repr(txt[idx:idx+400]))
