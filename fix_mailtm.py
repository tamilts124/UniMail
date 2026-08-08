b = open('cli_mailtm.py', 'rb').read()
print('size:', len(b))
idx = b.find(b'Create new account')
print('anchor idx:', idx)
if idx >= 0:
    print(repr(b[idx:idx+300]))
else:
    # try partial
    for kw in [b'new account', b'/accounts', b'password']:
        i = b.find(kw)
        print(kw, i, repr(b[max(0,i-5):i+50]) if i>=0 else 'NF')

# find password = line
b = open('cli_mailtm.py', 'rb').read()
for kw in [b'# Create new account\n', b'password = "".join', b'_mailtm_post(s, "/accounts"']:
    i = b.find(kw)
    print(repr(kw), '->', i)
    if i >= 0:
        print(repr(b[i:i+200]))
        print()

# ── Apply fix to cli_mailtm.py ──
b = open('cli_mailtm.py', 'rb').read()

OLD = (
    b'    # Create new account\n'
    b'    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))\n'
    b'    body, status = _mailtm_post(s, "/accounts", {"address": email_key, "password": password})\n'
    b'    if status not in (200, 201) or not body.get("id"):\n'
    b'        raise RuntimeError(f"mail.tm: /accounts creation failed (HTTP {status}): {body}")\n'
    b'\n'
    b'    account_id = body["id"]\n'
    b'    token = _mailtm_get_token(s, email_key, password)\n'
    b'\n'
    b'    _mailtm_pool[email_key] = {"session": s, "token": token, "account_id": account_id}\n'
    b'    _mailtm_save(email_key, s, token, account_id, password, cache)\n'
    b'    dbg(f"mailtm: created account {email_key} (id={account_id})")\n'
    b'    return s, token, account_id\n'
)

NEW = (
    b'    # Create new account -- fetch live domain in case seed has rotated\n'
    b'    live_domains = mailtm_get_domains(s)\n'
    b'    req_domain = email_key.split("@")[1] if "@" in email_key else ""\n'
    b'    user_part  = email_key.split("@")[0]\n'
    b'    if live_domains and req_domain not in live_domains:\n'
    b'        address = f"{user_part}@{live_domains[0]}"\n'
    b'        dbg(f"mailtm: domain \'{req_domain}\' not active, using live domain \'{live_domains[0]}\'")\n'
    b'    else:\n'
    b'        address = email_key\n'
    b'    password = "".join(random.choices(string.ascii_letters + string.digits, k=16))\n'
    b'    body, status = _mailtm_post(s, "/accounts", {"address": address, "password": password})\n'
    b'    if status not in (200, 201) or not body.get("id"):\n'
    b'        raise RuntimeError(f"mail.tm: /accounts creation failed (HTTP {status}): {body}")\n'
    b'\n'
    b'    account_id = body["id"]\n'
    b'    real_addr  = address  # may differ from email_key if domain was remapped\n'
    b'    token = _mailtm_get_token(s, real_addr, password)\n'
    b'\n'
    b'    _mailtm_pool[real_addr] = {"session": s, "token": token, "account_id": account_id}\n'
    b'    _mailtm_save(real_addr, s, token, account_id, password, cache)\n'
    b'    # also store a redirect in cache so the original key resolves\n'
    b'    if real_addr != email_key:\n'
    b'        mb2 = cache.setdefault("mailboxes", {}).setdefault(email_key, {})\n'
    b'        mb2["redirect_to"] = real_addr\n'
    b'        from cli_config import save_cache\n'
    b'        save_cache(cache)\n'
    b'    dbg(f"mailtm: created account {real_addr} (id={account_id})")\n'
    b'    return s, token, account_id\n'
)

if OLD in b:
    b2 = b.replace(OLD, NEW)
    open('cli_mailtm.py', 'wb').write(b2)
    print('cli_mailtm.py fixed OK')
else:
    print('OLD block NOT FOUND in cli_mailtm.py')

# ── Fix 3: cli_commands.py — fix cmd_list_domain for mail.tm ──
b = open('cli_commands.py', 'rb').read()
print('cli_commands.py size:', len(b))

OLD_CMD = (
    b'    try:\r\n'
    b'        if site_name == "tempmailq.com":\r\n'
    b'            s = _tmq_new_session()\r\n'
    b'            resp = s.get(TEMPMAILQ_BASE + "/", timeout=HTTP_TIMEOUT)\r\n'
    b'            body_text = resp.text\r\n'
    b'        else:\r\n'
    b'            _, body_text = maildax_fetch_csrf()\r\n'
    b'        found = re.findall(r\'<option[^>]*value=["\\\']([ a-z0-9.-]+\\.[a-z]{2,})["\\\']\', body_text)\r\n'
    b'        if not found:\r\n'
    b'            found = re.findall(r\'@([a-z0-9-]+\\.[a-z]{2,})\', body_text)\r\n'
    b'        if found:\r\n'
    b'            domains = list(dict.fromkeys(found))\r\n'
    b'        if domains != SITE_DOMAINS[site_name]:\r\n'
    b'            SITE_DOMAINS[site_name] = domains\r\n'
    b'            for d in domains:\r\n'
    b'                DOMAIN_MAP[d] = site_name\r\n'
    b'    except Exception as e:\r\n'
    b'        warn(f"Could not fetch live domain list ({e}), showing cached.")\r\n'
)

print('OLD_CMD found:', OLD_CMD in b)
# show actual bytes at that region
idx = b.find(b'if site_name == "tempmailq.com"')
print('tempmailq block at:', idx)
if idx >= 0:
    print(repr(b[idx-10:idx+500]))

# ── Apply Fix 3: cli_commands.py cmd_list_domain — add mail.tm branch ──
b = open('cli_commands.py', 'rb').read()

OLD3 = (
    b'        if site_name == "tempmailq.com":\r\n'
    b'            s = _tmq_new_session()\r\n'
    b'            resp = s.get(TEMPMAILQ_BASE + "/", timeout=HTTP_TIMEOUT)\r\n'
    b'            body_text = resp.text\r\n'
    b'        else:\r\n'
    b'            _, body_text = maildax_fetch_csrf()\r\n'
    b'        found = re.findall(r\'<option[^>]*value=["\\\']([ a-z0-9.-]+\\.[a-z]{2,})["\\\']\', body_text)\r\n'
    b'        if not found:\r\n'
    b'            found = re.findall(r\'@([a-z0-9-]+\\.[a-z]{2,})\', body_text)\r\n'
    b'        if found:\r\n'
    b'            domains = list(dict.fromkeys(found))\r\n'
    b'        if domains != SITE_DOMAINS[site_name]:\r\n'
    b'            SITE_DOMAINS[site_name] = domains\r\n'
    b'            for d in domains:\r\n'
    b'                DOMAIN_MAP[d] = site_name\r\n'
)

# Get exact bytes from file
idx = b.find(b'if site_name == "tempmailq.com"')
block = b[idx:idx+700]
print(repr(block[:500]))
