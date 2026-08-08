#!/usr/bin/env python3
"""Session-4 tests: maildrop.cc, temp-mail.io, mailinator API check."""
import sys, json
sys.path.insert(0, r'D:\ClaudeDir\tempmail')

from curl_cffi import requests as rq

OUT = []

def log(msg):
    OUT.append(msg)
    print(msg, flush=True)

# ── 1. maildrop.cc GraphQL ─────────────────────────────────────────────────
log("=== maildrop.cc ===")
s = rq.Session(impersonate='chrome124')
s.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'https://maildrop.cc',
    'Referer': 'https://maildrop.cc/',
})
try:
    r = s.post('https://api.maildrop.cc/graphql',
               json={'query': '{ inbox(mailbox: "testclaude2026") { id mailfrom headerfrom subject date } }'},
               timeout=20)
    log(f"maildrop inbox status: {r.status_code}")
    log(f"maildrop inbox body: {r.text[:400]}")
except Exception as e:
    log(f"maildrop ERROR: {e}")

# ── 2. temp-mail.io API ────────────────────────────────────────────────────
log("\n=== temp-mail.io ===")
s2 = rq.Session(impersonate='chrome124')
s2.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Origin': 'https://temp-mail.io',
    'Referer': 'https://temp-mail.io/',
})
try:
    r2 = s2.post('https://api.internal.temp-mail.io/api/v3/email/new',
                 json={}, timeout=20)
    log(f"temp-mail.io create status: {r2.status_code}")
    log(f"temp-mail.io create body: {r2.text[:400]}")
    if r2.status_code == 200:
        data = r2.json()
        addr = data.get('email') or data.get('address', '')
        log(f"temp-mail.io assigned address: {addr}")
        if addr:
            r3 = s2.get(f'https://api.internal.temp-mail.io/api/v3/email/{addr}/messages',
                        timeout=20)
            log(f"temp-mail.io list status: {r3.status_code}")
            log(f"temp-mail.io list body: {r3.text[:400]}")
except Exception as e:
    log(f"temp-mail.io ERROR: {e}")

# ── 3. mailinator.com check ────────────────────────────────────────────────
log("\n=== mailinator.com (API key check) ===")
s3 = rq.Session(impersonate='chrome124')
try:
    r4 = s3.get('https://api.mailinator.com/api/v2/domains/mailinator.com/inboxes/testclaude2026',
                headers={'Accept': 'application/json',
                         'Referer': 'https://www.mailinator.com/'},
                timeout=10)
    log(f"mailinator status: {r4.status_code}")
    log(f"mailinator body: {r4.text[:200]}")
except Exception as e:
    log(f"mailinator ERROR: {e}")

with open(r'D:\ClaudeDir\tempmail\err.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
log("DONE - results in err.txt")
