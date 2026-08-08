#!/usr/bin/env python3
import requests
import sys

HDR = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, */*',
}

def probe(name, url, method='GET', data=None):
    try:
        if method == 'POST':
            r = requests.post(url, json=data, headers=HDR, timeout=12)
        else:
            r = requests.get(url, headers=HDR, timeout=12)
        print(f'[{name}] {r.status_code}: {r.text[:300]}')
    except Exception as e:
        print(f'[{name}] ERROR: {e}')
    sys.stdout.flush()

probe('catchmail', 'https://catchmail.io/api/v1/mailbox?address=testx99@catchmail.io')
probe('tempmail.lol', 'https://api.tempmail.lol/generate', 'POST')
probe('tempmail.plus mails', 'https://tempmail.plus/api/mails?eml=testx99&limit=20')
probe('tempmail.plus new', 'https://tempmail.plus/api/mail', 'POST', {'eml': 'testx99'})
probe('muellmail home', 'https://www.muellmail.com/')
probe('rainmail home', 'https://rainmail.xyz/')
probe('noopmail home', 'https://noopmail.org/')
probe('temp-mail.gg home', 'https://temp-mail.gg/')
