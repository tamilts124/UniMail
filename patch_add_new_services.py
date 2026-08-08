#!/usr/bin/env python3
"""
Patch cli_config.py to add 1secmail.com and tempmail.lol entries.
"""

config_path = r'D:\ClaudeDir\tempmail\cli_config.py'

with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add 1secmail.com to SITE_DOMAINS (after the tempmailo.com entry)
old_tempmailo_entry = '''    # -- tempmailo.com -- ASP.NET Core + Cloudflare, address server-assigned ----
    # GET  / -> scrape __RequestVerificationToken hidden field; sets antiforgery + cf_clearance cookies
    # GET  /changemail?_r=<rand> (header: RequestVerificationToken) -> plain-text assigned email
    # GET  /changemail?tmail=<email>&_r=<rand> -> confirm/restore existing address
    # POST / (header: RequestVerificationToken, body JSON {mail:<email>}) -> messages[]
    # Domains rotate; denipl.net and fxzig.com observed 2026-07-19.
    "tempmailo.com": ["denipl.net", "denipl.com", "fxzig.com"],
}'''

# Find the closing brace of SITE_DOMAINS (the line with just "}")
# We'll insert before it
site_domains_close = '    "tempmailo.com": ["denipl.net", "denipl.com", "fxzig.com"],\n}'

new_site_domains_additions = '''    "tempmailo.com": ["denipl.net", "denipl.com", "fxzig.com"],
    # -- 1secmail.com -- public REST API, fully stateless, no auth needed --------
    # GET /api/v1/?action=getMessages&login=<user>&domain=<domain> -> [{id,from,subject,date}]
    # GET /api/v1/?action=readMessage&login=<user>&domain=<domain>&id=<id> -> full msg
    # GET /api/v1/?action=genRandomMailbox&count=1 -> ["user@domain.com"]
    # GET /api/v1/?action=getDomainList -> ["1secmail.com", "1secmail.org", ...]
    # Completely stateless: any user@supported_domain works, no session needed.
    "1secmail.com": [
        "1secmail.com", "1secmail.org", "1secmail.net",
        "wwjmp.com", "esiix.com", "xojxe.com", "yoggm.com",
    ],
    # -- tempmail.lol -- public REST API v2, free tier no API key needed ---------
    # POST https://api.tempmail.lol/v2/inbox/create -> {address, token, expires}
    # GET  https://api.tempmail.lol/v2/inbox?token=<token> -> {emails: [...]}
    # Free tier: inbox expires after 1 hour. No auth needed for free tier.
    "tempmail.lol": ["rcmails.com", "spambox.me", "qiott.com"],
}'''

if site_domains_close in content:
    content = content.replace(site_domains_close, new_site_domains_additions)
    print("Added 1secmail.com and tempmail.lol to SITE_DOMAINS")
else:
    print("ERROR: Could not find SITE_DOMAINS closing brace. Manual check needed.")
    print(f"Looking for: {repr(site_domains_close[:80])}")

# 2. Add ONESECMAIL_BASE and TEMPMAIL_LOL_BASE constants after TEMPMAILO_COM_BASE
old_base = '# tempmailo.com ASP.NET Core + Cloudflare (address server-assigned)\nTEMPMAILO_COM_BASE = "https://tempmailo.com"\n'
new_base = '''# tempmailo.com ASP.NET Core + Cloudflare (address server-assigned)
TEMPMAILO_COM_BASE = "https://tempmailo.com"
# 1secmail.com public REST API (fully stateless, no auth)
ONESECMAIL_BASE = "https://www.1secmail.com/api/v1/"
# tempmail.lol public REST API v2 (free tier, no API key needed)
TEMPMAIL_LOL_BASE = "https://api.tempmail.lol"
'''

if old_base in content:
    content = content.replace(old_base, new_base)
    print("Added ONESECMAIL_BASE and TEMPMAIL_LOL_BASE constants")
else:
    print("ERROR: Could not find TEMPMAILO_COM_BASE line")
    print(repr(old_base))

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("cli_config.py patched successfully.")
