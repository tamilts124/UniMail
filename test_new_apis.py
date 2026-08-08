#!/usr/bin/env python3
"""Quick test of 1secmail and tempmail.lol API endpoints."""
import requests, json

print("=== 1secmail.com API Test ===")
# 1. Get domain list
r = requests.get("https://www.1secmail.com/api/v1/", params={"action": "getDomainList"}, timeout=10)
print(f"getDomainList: {r.status_code} -> {r.text[:200]}")

# 2. Generate random address
r2 = requests.get("https://www.1secmail.com/api/v1/", params={"action": "genRandomMailbox", "count": 1}, timeout=10)
print(f"genRandomMailbox: {r2.status_code} -> {r2.text[:200]}")
if r2.status_code == 200:
    addresses = r2.json()
    if addresses:
        addr = addresses[0]
        login, domain = addr.split("@", 1)
        print(f"Generated: {addr}")
        
        # 3. Check inbox
        r3 = requests.get("https://www.1secmail.com/api/v1/", 
            params={"action": "getMessages", "login": login, "domain": domain}, timeout=10)
        print(f"getMessages: {r3.status_code} -> {r3.text[:200]}")

print()
print("=== tempmail.lol API Test ===")
# Try v2 API
r4 = requests.post("https://api.tempmail.lol/v2/inbox/create", 
    headers={"Accept": "application/json"}, timeout=10)
print(f"POST /v2/inbox/create: {r4.status_code} -> {r4.text[:300]}")

# Try v1 generate
r5 = requests.get("https://api.tempmail.lol/generate", 
    headers={"Accept": "application/json"}, timeout=10)
print(f"GET /generate: {r5.status_code} -> {r5.text[:300]}")
