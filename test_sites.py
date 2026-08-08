#!/usr/bin/env python3
"""Test all 4 new Laravel sites live."""
import sys, time
sys.path.insert(0, '.')
from cli_config import load_cache, save_cache
from cli_tmq import _tmq_new_session, _tmq_seed, _tmq_post, _tmq_get_session, _tmq_call

def test_site(base_url, user, domain, label):
    print(f"\n=== {label} ===")
    s = _tmq_new_session(base_url)
    try:
        xsrf, meta = _tmq_seed(s, base_url)
        print(f"  seed OK: xsrf={xsrf[:20]!r}... meta={meta[:20]!r}...")
    except Exception as e:
        print(f"  seed FAILED: {e}")
        return

    try:
        body0, xsrf, meta = _tmq_post(s, base_url, '/get_messages', {}, xsrf, meta)
        print(f"  /get_messages: {str(body0)[:200]}")
    except Exception as e:
        print(f"  /get_messages FAILED: {e}")
        return

    try:
        body1, xsrf, meta = _tmq_post(s, base_url, '/change', {'name': user, 'domain': domain}, xsrf, meta)
        print(f"  /change: {str(body1)[:200]}")
    except Exception as e:
        print(f"  /change FAILED: {e}")

# Test each site
test_site('https://temporarymailservice.com', 'testclaude99', 'tomail.fyi', 'temporarymailservice.com')
test_site('https://zhimail.xyz', 'testclaude99', 'zhimails.work', 'zhimail.xyz')
test_site('https://mailditch.com', 'testclaude99', 'ditch.my.id', 'mailditch.com')
test_site('https://tempmaili.com', 'testclaude99', 'munik.edu.pl', 'tempmaili.com')

print("\nDone.")
