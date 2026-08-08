#!/usr/bin/env python3
"""Probe mailmomy.com - get all domains and test full flow."""
import requests, json

BASE = "https://mailmomy.com"
HDR  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}

# Get all domains
r = requests.get(f"{BASE}/api/domains", headers=HDR, timeout=10)
domains_data = r.json()
active_domains = [d['domain'] for d in domains_data if d.get('active')]
print(f"Active domains ({len(active_domains)}):", active_domains)

# Test message fetch with first active domain
if active_domains:
    test_email = f"testclaude@{active_domains[0]}"
    r2 = requests.get(f"{BASE}/api/mail/messages", params={"to": test_email, "page": 1, "limit": 5}, headers=HDR, timeout=10)
    print(f"\nInbox {test_email}: {r2.status_code} -> {r2.text[:200]}")

# Test single message read by ID (we need a real ID but can test structure)
print("\n=== Test delete single message ===")
r3 = requests.delete(f"{BASE}/api/mail/delete", params={"id": "fake-uuid-000"}, headers=HDR, timeout=8)
print(f"DELETE by id: {r3.status_code} -> {r3.text[:150]}")
