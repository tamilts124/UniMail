#!/usr/bin/env python3
"""Seed tempemail.cc credentials into unimail cache."""
import json, sys

CACHE = r"D:\ClaudeDir\tempmail\.unimail_cache.json"
KEY   = "naia2022@icmans.com"
DATA  = {
    "tempemail_token":      "eyJhbGciOiJFZERTQSJ9.eyJpYXQiOjE3ODQ0NzU5MDEsImlkIjoiMjA0NzQyMzMwMjE1ODI5NTA0Iiwib3duZXJJZCI6IjIwNDc0MjMzMDIxNTgyOTUwNCIsIm1haWxib3hUeXBlIjowLCJtZXJjdXJlIjp7InN1YnNjcmliZSI6WyIvdS8yMDQ3NDIzMzAyMTU4Mjk1MDQiXX19.x1imokXcJV0LUUpT-lehWAhcYzGZ-lFbQ9uyprMbftzzNWxDDXG_VTzxWQIOh44Awk8IupjHsA8-Ewpmaw7JAQ",
    "tempemail_account_id": "204742330215829504",
    "tempemail_password":   "PpJ*h8wGl9",
}

try:
    with open(CACHE, encoding="utf-8") as f:
        cache = json.load(f)
    cache.setdefault("mailboxes", {})[KEY] = DATA
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    # Verify
    with open(CACHE, encoding="utf-8") as f:
        c2 = json.load(f)
    mb = c2["mailboxes"].get(KEY, {})
    tok = mb.get("tempemail_token", "MISSING")
    sys.stdout.write(f"OK — token starts: {tok[:30]}\n")
except Exception as exc:
    sys.stderr.write(f"FAIL: {exc}\n")
    sys.exit(1)
