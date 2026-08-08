import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('cli_fakemail.py', encoding='utf-8') as f:
    txt = f.read()

OLD = '    body = resp2.json()\n    assigned_email = body.get("email"'
NEW = '    # Strip UTF-8 BOM before JSON parse (server sends \\xef\\xbb\\xbf prefix)\n    import json as _json\n    body = _json.loads(resp2.content.lstrip(b"\\xef\\xbb\\xbf"))\n    assigned_email = body.get("email"'

if OLD in txt:
    txt2 = txt.replace(OLD, NEW, 1)
    with open('cli_fakemail.py', 'w', encoding='utf-8') as f:
        f.write(txt2)
    print("Patched cli_fakemail.py OK")
else:
    print("Pattern not found!")
    print(repr(txt[txt.find('resp2.json'):txt.find('resp2.json')+100]))
