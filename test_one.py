#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from cli_tmq import _tmq_new_session, _tmq_seed, _tmq_post

base = sys.argv[1]
user = sys.argv[2]
domain = sys.argv[3]

print(f"Testing {base} -> {user}@{domain}")
s = _tmq_new_session(base)
xsrf, meta = _tmq_seed(s, base)
print(f"seed OK xsrf={xsrf[:15]!r} meta={meta[:15]!r}")
body0, xsrf, meta = _tmq_post(s, base, '/get_messages', {}, xsrf, meta)
print(f"get_messages: {str(body0)[:300]}")
body1, xsrf, meta = _tmq_post(s, base, '/change', {'name': user, 'domain': domain}, xsrf, meta)
print(f"change: {str(body1)[:300]}")
