#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from cli_config import load_cache
from cli_tmq import _tmq_call

email = sys.argv[1]
cache = load_cache()
body = _tmq_call(email, '/get_messages', {}, cache)
msgs = body.get('messages', [])
print(f'Messages for {email}: {len(msgs)}')
for m in msgs[:5]:
    subj = m.get('subject', '(no subject)')
    frm = m.get('from') or m.get('from_email', 'unknown')
    print(f'  - {subj} | from: {frm}')
print('Done.')

# guerrillamail test stub below
