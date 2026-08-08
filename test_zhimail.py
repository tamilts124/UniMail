#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from cli_tmq import _tmq_new_session, _tmq_seed, _tmq_post
import socket
socket.setdefaulttimeout(15)

base = 'https://zhimail.xyz'
user = 'testclaude99'
domain = 'zhimails.work'

print(f"Testing {base} -> {user}@{domain}", flush=True)
try:
    s = _tmq_new_session(base)
    xsrf, meta = _tmq_seed(s, base)
    print(f"seed OK xsrf={xsrf[:15]!r} meta={meta[:15]!r}", flush=True)
    body0, xsrf, meta = _tmq_post(s, base, '/get_messages', {}, xsrf, meta)
    print(f"get_messages: {str(body0)[:300]}", flush=True)
    body1, xsrf, meta = _tmq_post(s, base, '/change', {'name': user, 'domain': domain}, xsrf, meta)
    print(f"change: {str(body1)[:300]}", flush=True)
except Exception as e:
    print(f"FAILED: {e}", flush=True)
