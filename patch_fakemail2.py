import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('cli_fakemail.py', encoding='utf-8') as f:
    txt = f.read()

# Patch 1: resp3.json() in new-email fallback
OLD1 = '        if resp3.status_code == 200:\n            body3 = resp3.json()\n            assigned_email = body3.get("email"'
NEW1 = '        if resp3.status_code == 200:\n            import json as _json\n            body3 = _json.loads(resp3.content.lstrip(b"\\xef\\xbb\\xbf"))\n            assigned_email = body3.get("email"'

# Patch 2: /index/refresh result = resp.json()
OLD2 = '    result = resp.json()\n    # Server returns 0 (int) when empty'
NEW2 = '    # Strip UTF-8 BOM before JSON parse\n    import json as _json\n    result = _json.loads(resp.content.lstrip(b"\\xef\\xbb\\xbf"))\n    # Server returns 0 (int) when empty'

# Patch 3: /index/email return resp.json()
OLD3 = '    dbg(f"fakemail: POST /index/email id={msg_id} -> {resp.status_code}")\n    if resp.status_code != 200:\n        raise RuntimeError(f"fakemail: /index/email failed (HTTP {resp.status_code})")\n    return resp.json()'
NEW3 = '    dbg(f"fakemail: POST /index/email id={msg_id} -> {resp.status_code}")\n    if resp.status_code != 200:\n        raise RuntimeError(f"fakemail: /index/email failed (HTTP {resp.status_code})")\n    import json as _json\n    return _json.loads(resp.content.lstrip(b"\\xef\\xbb\\xbf"))'

count = 0
for old, new in [(OLD1, NEW1), (OLD2, NEW2), (OLD3, NEW3)]:
    if old in txt:
        txt = txt.replace(old, new, 1)
        count += 1
        print(f"Patch applied: {old[:50]!r}...")
    else:
        print(f"Pattern NOT found: {old[:50]!r}...")

with open('cli_fakemail.py', 'w', encoding='utf-8') as f:
    f.write(txt)
print(f"Done: {count} patch(es) applied")
