#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from cli_config import load_cache, set_debug
set_debug(True)
cache = load_cache()

# ── 1. freecustom.email ───────────────────────────────────────────────────────
print('=== freecustom.email ===')
try:
    from cli_freecustom import freecustom_get_token, freecustom_list_messages
    token = freecustom_get_token(cache)
    print(f'  token OK: {token[:20]}...')
    msgs = freecustom_list_messages('testclaude3@addmy.space', cache)
    print(f'  inbox testclaude3@addmy.space: {len(msgs)} msg(s)')
    for m in msgs[:3]:
        print(f'    - {m.get("subject","?")} from {m.get("from","?")} @ {m.get("date","?")}')
except Exception as e:
    print(f'  ERROR: {e}')

# ── 2. tempemail.cc ───────────────────────────────────────────────────────────
print('=== tempemail.cc ===')
try:
    from cli_tempemail import tempemail_create_new
    s2, addr2 = tempemail_create_new(cache)
    print(f'  created: {addr2}')
except Exception as e:
    print(f'  ERROR (expected if rate-limited): {e}')

# ── 3. fakemail.net ───────────────────────────────────────────────────────────
print('=== fakemail.net ===')
try:
    from cli_fakemail import fakemail_get_session, fakemail_list_messages
    s3, csrf3 = fakemail_get_session('test@forliion.com', cache)
    real = cache.get('mailboxes', {}).get('test@forliion.com', {})
    assigned = real.get('redirect_to', 'test@forliion.com')
    print(f'  session OK, assigned: {assigned}')
    msgs3 = fakemail_list_messages(assigned, cache)
    print(f'  inbox {assigned}: {len(msgs3)} msg(s)')
except Exception as e:
    print(f'  ERROR: {e}')

print('DONE')
