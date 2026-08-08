#!/usr/bin/env python3
"""Analyze HAR files for temporarymailservice, zhimail, mailditch, tempmaili."""
import json, sys, os

har_dir = r"D:\ClaudeDir\tempmail\har"
files = [
    "temporarymailservice.com.json",
    "zhimail.xyz.json",
    "mailditch.com.json",
    "tempmaili.com.json",
]

for fname in files:
    fpath = os.path.join(har_dir, fname)
    if not os.path.exists(fpath):
        print(f"MISSING: {fpath}")
        continue
    print(f"\n{'='*70}")
    print(f"FILE: {fname}")
    print(f"{'='*70}")
    with open(fpath) as f:
        har = json.load(f)
    entries = har['log']['entries']
    print(f"Total HAR entries: {len(entries)}")
    for i, e in enumerate(entries):
        req = e['request']
        resp = e['response']
        url = req['url']
        method = req['method']
        status = resp['status']
        print(f"\n  [{i}] {method} {url} -> {status}")
        # show request headers of interest
        for h in req.get('headers', []):
            if h['name'].lower() in ('x-xsrf-token','content-type','referer','x-requested-with','accept'):
                print(f"       REQ HDR {h['name']}: {h['value'][:80]}")
        if req.get('postData'):
            pd = req['postData']
            body = pd.get('text', '') or ''
            print(f"       POST BODY: {body[:400]}")
        ct = resp.get('content', {}).get('mimeType', '')
        txt = resp.get('content', {}).get('text', '') or ''
        if txt:
            print(f"       RESP ({ct}): {txt[:400]}")
        # show set-cookie response headers
        for h in resp.get('headers', []):
            if h['name'].lower() == 'set-cookie':
                print(f"       SET-COOKIE: {h['value'][:120]}")
