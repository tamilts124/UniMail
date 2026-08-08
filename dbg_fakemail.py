import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open('cli_fakemail.py', encoding='utf-8') as f:
    txt = f.read()
# find the code section (not docstring)
idx = txt.find('resp2.json()')
print(repr(txt[idx-300:idx+50]))
