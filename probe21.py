from curl_cffi import requests as cr

results = []
tests = [
    ('https://api.mail.gw/domains', 'mail.gw domains'),
    ('https://api.mail.gw/messages', 'mail.gw messages (no auth)'),
    ('https://48hr.email/api/inbox/testclaude', '48hr.email inbox'),
    ('https://48hr.email/api/email', '48hr.email generate'),
    ('https://48hr.email/api/', '48hr.email api root'),
]
for url, label in tests:
    try:
        r = cr.get(url, timeout=8, impersonate='chrome124')
        results.append(f"{label}: {r.status_code} | {r.text[:200]}")
    except Exception as e:
        results.append(f"{label}: ERR {str(e)[:80]}")

open('probe21_out.txt', 'w', encoding='utf-8').write('\n'.join(results))
print("done")
