#!/usr/bin/env python3
"""Test if we can get address from GET / HTML directly."""
import re, sys
from curl_cffi import requests as curl_requests

BASE = "https://tempmailo.com"
s = curl_requests.Session(impersonate="chrome124")
resp = s.get(BASE + "/", timeout=20)
print(f"Status: {resp.status_code}", flush=True)

# Look for the email address in the page HTML
text = resp.text
# Search for email addresses
emails = re.findall(r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}', text, re.IGNORECASE)
print(f"Emails found in HTML: {emails[:5]}", flush=True)

# Look for tempMailoN or similar
m = re.search(r'tempMailoN["\s]*[:=]["\s]*([^"\'<>\s]+)', text)
print(f"tempMailoN in HTML: {m.group(1) if m else 'NOT_FOUND'}", flush=True)

# Look for value in any input that looks like email
inputs = re.findall(r'<input[^>]*value="([^"]*@[^"]*)"[^>]*>', text)
print(f"Email inputs: {inputs}", flush=True)

# Print a snippet around 'mail' or 'email' 
for kw in ['denipl', 'fxzig', 'tmail']:
    idx = text.find(kw)
    if idx >= 0:
        print(f"Found '{kw}' at {idx}: ...{text[max(0,idx-30):idx+80]}...", flush=True)
