#!/usr/bin/env python3
"""
cli_commands.py - all --flag command implementations for the unimail.py CLI.
"""

import sys, re, textwrap, html

from cli_config import (
    c, header, info, warn, err, ok, dbg,
    SITE_DOMAINS, DOMAIN_MAP, TEMPMAILQ_BASE, MAILDAX_BASE,
    CHATWORKON_BASE, TEMPMAILSALL_BASE, DAKBOX_BASE, TEMPMAILWORLD_BASE,
    DISPOSABLE_BASE, HTTP_TIMEOUT, parse_email, save_cache,
    LARAVEL_SITES,
    TEMPORARYMAILSERVICE_BASE, ZHIMAIL_BASE, MAILDITCH_BASE, TEMPMAILI_BASE,
    MAILTM_BASE, GUERRILLA_BASE, TENMINMAIL_BASE, OPENINBOX_BASE,
    MAILINATOR_BASE, MAILDROP_BASE, TEMPMAILIO_BASE, TEMPEMAIL_BASE,
    FREECUSTOM_BASE, FAKEMAIL_BASE, TEMPFORWARD_BASE,
    TEMPMAILO_COM_BASE, CATCHMAIL_BASE, TEMPMAILPLUS_BASE,
    MOHMAL_BASE,
)

from cli_mohmal import (
    mohmal_create_session, mohmal_list_messages, mohmal_get_message, mohmal_delete_session,
)



from cli_mailmomy import (
    mailmomy_list_messages, mailmomy_delete_all, mailmomy_delete_message,
)



from cli_tempemail import (
    tempemail_create_new, tempemail_get_session, tempemail_list_messages,
    tempemail_get_message, tempemail_delete_message, tempemail_delete_account,
)
from cli_mailtm import (
    mailtm_get_session, mailtm_list_messages, mailtm_get_message,
    mailtm_delete_account, mailtm_get_domains,
)
from cli_guerrilla import (
    guerrilla_get_session, guerrilla_list_messages, guerrilla_get_message,
    guerrilla_delete_account,
)
from cli_10mm import (
    tenminmail_create_new, tenminmail_get_session, tenminmail_list_messages,
    tenminmail_delete_account,
)
from cli_openinbox import (
    openinbox_create_new, openinbox_get_session, openinbox_list_messages,
    openinbox_get_message, openinbox_delete_inbox,
)
from cli_tmq import (
    _tmq_new_session, _tmq_get_session, _tmq_call, _tmq_pool, _tmq_fetch_message_html,
)
from cli_maildax import maildax_fetch_csrf
from cli_cwo import (
    _cwo_get_session, cwo_list_mails, cwo_delete_local, cwo_parse_raw_email,
)
from cli_tms import (
    _tms_get_session, tms_list_mails, tms_get_message, tms_delete_mailbox,
)
from cli_mailinator import (
    mailinator_list_messages, mailinator_get_message, mailinator_extract_body,
    MAILINATOR_DOMAIN,
)
from cli_maildrop import (
    maildrop_list_messages, maildrop_get_message, maildrop_delete_message,
    MAILDROP_DOMAIN,
)
from cli_tempmailio import (
    tempmailio_create_new, tempmailio_get_session, tempmailio_list_messages,
    tempmailio_delete_message,
)
from cli_freecustom import (
    freecustom_get_token, freecustom_list_messages, freecustom_get_message,
)
from cli_fakemail import (
    fakemail_get_session, fakemail_list_messages, fakemail_get_message,
    fakemail_delete_message, fakemail_delete_account,
)
from cli_tempforward import (
    tempforward_create_new, tempforward_get_session, tempforward_list_messages,
    tempforward_get_message, tempforward_delete_account,
)
from cli_tempmailo_com import (
    tempmailo_com_create_new, tempmailo_com_get_session, tempmailo_com_list_messages,
    tempmailo_com_delete_account,
)
from cli_catchmail import (
    catchmail_list_messages, catchmail_get_message, catchmail_delete_message,
)
from cli_tempmail_plus import (
    tempmailplus_list_messages, tempmailplus_get_message, tempmailplus_delete_message,
)
from cli_eyepaste import (
    eyepaste_list_messages, eyepaste_get_message,
    EYEPASTE_DOMAIN,
)

from cli_48hremail import (
    hr48_list_messages, hr48_get_message,
    HR48_DOMAIN,
)
from cli_harakirimail import (
    harakirimail_list_messages, harakirimail_get_message,
)
from cli_minuteinbox import (
    minuteinbox_get_session, minuteinbox_list_messages,
    minuteinbox_get_message, minuteinbox_delete_message,
)

from cli_10mm_net import (
    tenminnet_create_session, tenminnet_get_session,
    tenminnet_list_messages, tenminnet_get_message, tenminnet_delete_session,
)
from cli_dropmail import (
    dropmail_create_session, dropmail_get_session,
    dropmail_list_messages, dropmail_get_message, dropmail_delete_session,
)
from cli_evilmail import (
    evilmail_create_inbox, evilmail_list_messages,
    EVILMAIL_DOMAIN,
)






def resolve_mock_id(email_key: str, cache: dict) -> str:
    mb = cache.get("mailboxes", {}).get(email_key, {})
    if isinstance(mb, dict) and "redirect_to" in mb:
        return mb["redirect_to"]
    return email_key


def cmd_help():
    print(f"""
{c('bold',c('cyan','╔══════════════════════════════════════════════════════╗'))}
{c('bold',c('cyan','║          UniMail CLI  ·  Single-Line Commands        ║'))}
{c('bold',c('cyan','╚══════════════════════════════════════════════════════╝'))}

{c('bold','INFO')}
  {c('yellow','--list-site')}
      List all supported sites and their domains.

  {c('yellow','--list-domain')} {c('cyan','<site>')}
      List available domains for a site.
      e.g.  --list-domain tempmailq.com

{c('bold','MAILBOX')}
  {c('yellow','--mail-id')} {c('cyan','<user@domain>')}
      Use or create a mailbox. Each address gets its own session.
      e.g.  --mail-id mytest@wqacmjaqe.xyz

  {c('yellow','--delete-id')} {c('cyan','<user@domain>')}
      Delete mailbox on server and remove from local cache.
      e.g.  --delete-id mytest@wqacmjaqe.xyz

  {c('yellow','--real-mail-id')} {c('cyan','<user@domain>')}
      Print the real mailbox ID mapped to a mock address.
      e.g.  --real-mail-id testmock123@edubd.edu.pl

{c('bold','DEBUG')}
  {c('yellow','--debug')}
      Show verbose request/response debug logging. Can be combined with
      any other command, anywhere in the args.
      e.g.  --debug --list-message mytest@wqacmjaqe.xyz

{c('bold','MESSAGES')}
  {c('yellow','--list-message')} {c('cyan','<user@domain>')}
      List all messages in a mailbox.
      e.g.  --list-message mytest@wqacmjaqe.xyz

  {c('yellow','--view-message')} {c('cyan','<user@domain>')} {c('cyan','<n>')}
      View message #n (1-based).
      e.g.  --view-message mytest@wqacmjaqe.xyz 2

{c('bold','KNOWN DOMAINS')}""")
    for domain, site in DOMAIN_MAP.items():
        print(f"  {c('cyan', domain)}  →  {site}")
    print()


def cmd_list_site():
    header("Supported Sites & Domains")
    for site, domains in SITE_DOMAINS.items():
        if site == "tempmailq.com": base = TEMPMAILQ_BASE
        elif site == "maildax.cc": base = MAILDAX_BASE
        elif site == "chatworkon.com": base = CHATWORKON_BASE
        elif site == "tempmailsall.com": base = TEMPMAILSALL_BASE
        elif site == "dakbox.net": base = DAKBOX_BASE
        elif site == "temp-mail-world.com": base = TEMPMAILWORLD_BASE
        elif site == "disposableemailgenerator.com": base = DISPOSABLE_BASE
        elif site == "temporarymailservice.com": base = TEMPORARYMAILSERVICE_BASE
        elif site == "zhimail.xyz": base = ZHIMAIL_BASE
        elif site == "mailditch.com": base = MAILDITCH_BASE
        elif site == "tempmaili.com": base = TEMPMAILI_BASE
        elif site == "mail.tm": base = MAILTM_BASE
        elif site == "guerrillamail.com": base = GUERRILLA_BASE
        elif site == "10minutemail.com": base = TENMINMAIL_BASE
        elif site == "openinbox.io": base = OPENINBOX_BASE
        elif site == "mailinator.com": base = MAILINATOR_BASE
        elif site == "maildrop.cc": base = MAILDROP_BASE
        elif site == "temp-mail.io": base = TEMPMAILIO_BASE
        elif site == "tempemail.cc": base = TEMPEMAIL_BASE
        elif site == "freecustom.email": base = FREECUSTOM_BASE
        elif site == "tempforward.com": base = TEMPFORWARD_BASE
        elif site == "mailmomy.com": base = "https://mailmomy.com"
        elif site == "catchmail.io": base = "https://catchmail.io"
        elif site == "tempmail.plus": base = "https://tempmail.plus"
        elif site == "mohmal.com": base = MOHMAL_BASE
        elif site == "eyepaste.com":    base = "https://www.eyepaste.com"
        elif site == "48hr.email":      base = "https://48hr.email"
        elif site == "harakirimail.com": base = "https://harakirimail.com"
        elif site == "minuteinbox.com": base = "https://www.minuteinbox.com"
        elif site == "evilmail.pro":    base = "https://evilmail.pro"



        else: base = ""


        print(f"\n  {c('bold', site)}  {c('dim', base)}")
        for d in domains:
            print(f"    {c('dim','▸')} {d}")
    print()


def cmd_list_domain(site_name: str):
    site_name = site_name.lower()
    if site_name not in SITE_DOMAINS:
        err(f"Unknown site '{site_name}'. Known: {', '.join(SITE_DOMAINS)}")
        sys.exit(1)

    header(f"Domains for {site_name}")
    domains = SITE_DOMAINS[site_name]
    try:
        if site_name == "tempmailq.com":
            s = _tmq_new_session()
            resp = s.get(TEMPMAILQ_BASE + "/", timeout=HTTP_TIMEOUT)
            body_text = resp.text
        else:
            _, body_text = maildax_fetch_csrf()
        found = re.findall(r'<option[^>]*value=["\']([a-z0-9.-]+\.[a-z]{2,})["\']', body_text)
        if not found:
            found = re.findall(r'@([a-z0-9-]+\.[a-z]{2,})', body_text)
        if found:
            domains = list(dict.fromkeys(found))
        if domains != SITE_DOMAINS[site_name]:
            SITE_DOMAINS[site_name] = domains
            for d in domains:
                DOMAIN_MAP[d] = site_name
    except Exception as e:
        warn(f"Could not fetch live domain list ({e}), showing cached.")

    for d in domains:
        print(f"  {c('dim','▸')} {d}")
    print()


def cmd_mail_id(email_raw: str, cache: dict):
    user_raw, domain_raw, site_raw = parse_email(email_raw)
    email_raw_key = f"{user_raw}@{domain_raw}"
    email_key = resolve_mock_id(email_raw_key, cache)
    user, domain, site = parse_email(email_key)

    header(f"Mailbox: {email_key}")

    if site == "chatworkon.com":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("jwt"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                _cwo_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email",       email_key)
                info("JWT Token",   mb.get("jwt")[:25] + "...")
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating session on server …")
        try:
            _cwo_get_session(email_key, cache)
        except RuntimeError as e:
            err(str(e))
            sys.exit(1)

        mb = cache["mailboxes"][email_key]
        real_addr = mb.get("address", email_key)
        if real_addr != email_raw_key:
            cache["mailboxes"][email_raw_key] = {"redirect_to": real_addr}
            save_cache(cache)
        ok(f"Created: {c('cyan', real_addr)}")
        info("JWT Token", mb.get("jwt")[:25] + "...")
        print()
        return

    if site == "tempmailsall.com":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("session_id") and mb.get("nonce"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                _tms_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email",       email_key)
                info("Session ID",  mb.get("session_id")[:25] + "...")
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating session on server …")
        try:
            _, _, _, real_addr = _tms_get_session(email_key, cache)
        except RuntimeError as e:
            err(str(e))
            sys.exit(1)

        mb = cache["mailboxes"][real_addr]
        if real_addr != email_raw_key:
            cache["mailboxes"][email_raw_key] = {"redirect_to": real_addr}
            save_cache(cache)
        ok(f"Created: {c('cyan', real_addr)}")
        info("Session ID", mb.get("session_id")[:25] + "...")
        print()
        return

    if site == "mail.tm":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("mailtm_token") and mb.get("mailtm_account_id"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                mailtm_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email",      email_key)
                info("Account ID", mb.get("mailtm_account_id", "(unknown)"))
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating account on mail.tm …")
        try:
            _, token, account_id = mailtm_get_session(email_key, cache)
        except RuntimeError as e:
            err(str(e))
            sys.exit(1)
        ok(f"Created: {c('cyan', email_key)}")
        info("Account ID", account_id)
        print()
        return

    if site == "guerrillamail.com":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("guerrilla_sid_token"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                guerrilla_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email", email_key)
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating guerrillamail session ...")
        try:
            guerrilla_get_session(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', email_key)}")
        print()
        return

    if site == "openinbox.io":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("openinbox_id"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                openinbox_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email",      email_key)
                info("Inbox ID",   mb.get("openinbox_id", "(unknown)"))
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating new openinbox.io inbox ...")
        try:
            _, inbox_id, assigned_email = openinbox_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', assigned_email)}")
        info("Inbox ID", inbox_id)
        info("Note", "Address is server-assigned; use this address to receive mail")
        if assigned_email != email_key:
            cache["mailboxes"][email_key] = {"redirect_to": assigned_email}
            save_cache(cache)
            info("Redirect", f"{email_key} -> {assigned_email}")
        print()
        return

    if site == "10minutemail.com":
        # 10minutemail assigns addresses server-side — find or create
        # Check if we already have any 10mm address in cache
        cached_10mm = {k: v for k, v in cache.get("mailboxes", {}).items()
                       if isinstance(v, dict) and v.get("10mm_address")}
        if email_key in cached_10mm:
            mb = cached_10mm[email_key]
            info("Status", "Found in cache — validating session ...")
            try:
                _, address = tenminmail_get_session(email_key, cache)
                ok(f"Session alive: {c('cyan', address)}")
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), creating new ...")

        info("Status", "Creating new 10minutemail address ...")
        try:
            _, address = tenminmail_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', address)}")
        info("Note", "Address is server-assigned; use this address to receive mail")
        if address != email_key:
            cache["mailboxes"][email_key] = {"redirect_to": address}
            save_cache(cache)
            info("Redirect", f"{email_key} -> {address}")
        print()
        return

    if site == "mailinator.com":
        # Mailinator is stateless — any address is valid, no session to create
        header(f"Mailbox: {email_key}")
        ok(f"Mailinator inbox ready: {c('cyan', email_key)}")
        info("Note", "Mailinator is public and stateless — no session needed")
        info("Note", "Any email sent to this address is instantly readable")
        print()
        return

    if site == "maildrop.cc":
        # maildrop.cc is stateless — any address is valid, no session to create
        header(f"Mailbox: {email_key}")
        ok(f"Maildrop inbox ready: {c('cyan', email_key)}")
        info("Note", "Maildrop is public and stateless — no session needed")
        info("Note", "Messages expire after ~1 hour")
        print()
        return

    if site == "temp-mail.io":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("tempmailio_address"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                tempmailio_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email", mb.get("tempmailio_address", email_key))
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating new temp-mail.io inbox ...")
        try:
            _, address = tempmailio_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', address)}")
        info("Note", "Address is server-assigned; use this address to receive mail")
        if address != email_key:
            cache["mailboxes"][email_key] = {"redirect_to": address}
            save_cache(cache)
            info("Redirect", f"{email_key} -> {address}")
        print()
        return

    if site == "freecustom.email":
        try:
            freecustom_get_token(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Mailbox ready: {c('cyan', email_key)}")
        info("Note", "freecustom.email is stateless — no account creation needed")
        print()
        return

    if site == "tempemail.cc":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("tempemail_token") and mb.get("tempemail_account_id"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                tempemail_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email",      email_key)
                info("Account ID", mb.get("tempemail_account_id", "(unknown)"))
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating account on tempemail.cc …")
        try:
            _, address = tempemail_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', address)}")
        info("Note", "Address is server-assigned; use this address to receive mail")
        if address != email_key:
            cache["mailboxes"][email_key] = {"redirect_to": address}
            save_cache(cache)
            info("Redirect", f"{email_key} -> {address}")
        print()
        return

    if site == "fakemail.net":
        try:
            s, csrf = fakemail_get_session(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        real_addr = resolve_mock_id(email_key, cache)
        ok(f"Mailbox ready: {c('cyan', real_addr)}")
        info("Note", "Address is server-assigned (PHP session); use real address to receive mail")
        print()
        return

    if site == "tempforward.com":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("tempforward_token"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                s, token = tempforward_get_session(email_key, cache)
                ok("Session restored from cache.")
                info("Email", email_key)
                info("Token", token[:16] + "...")
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache — creating new tempforward.com inbox ...")
        try:
            s, address = tempforward_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', address)}")
        info("Note", "Address is server-assigned; use this address to receive mail")
        if address != email_key:
            cache["mailboxes"][email_key] = {"redirect_to": address}
            save_cache(cache)
            info("Redirect", f"{email_key} -> {address}")
        print()
        return


    if site == "tempmailo.com":
        mb = cache["mailboxes"].get(email_key, {})
        if mb.get("tempmailo_com_token") and mb.get("tempmailo_com_address"):
            dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
            try:
                s, token = tempmailo_com_get_session(email_key, cache)
                real_addr = mb.get("tempmailo_com_address", email_key)
                ok("Session restored from cache.")
                info("Email", real_addr)
                info("Token", token[:20] + "...")
                print()
                return
            except Exception as e:
                warn(f"Cache restore failed ({e}), re-creating ...")

        info("Status", "Not in cache - creating new tempmailo.com inbox ...")
        try:
            s, address = tempmailo_com_create_new(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        ok(f"Created: {c('cyan', address)}")
        info("Note", "Address is server-assigned (ASP.NET + Cloudflare)")
        if address != email_key:
            cache["mailboxes"].setdefault(email_key, {})["redirect_to"] = address
            save_cache(cache)
            info("Redirect", f"{email_key} -> {address}")
        print()
        return

    if site == "mailmomy.com":
        # mailmomy.com is fully stateless — any address is valid, no session to create
        header(f"Mailbox: {email_key}")
        ok(f"Mailmomy inbox ready: {c('cyan', email_key)}")
        info("Note", "mailmomy.com is public and stateless — no session needed")
        info("Note", "Full message body is included in inbox listing")
        print()
        return


    if site == "catchmail.io":
        header(f"Mailbox: {email_key}")
        ok(f"Catchmail inbox ready: {c('cyan', email_key)}")
        info("Note", "catchmail.io is public and stateless — no session needed")
        print()
        return

    if site == "tempmail.plus":
        header(f"Mailbox: {email_key}")
        ok(f"Tempmail.plus inbox ready: {c('cyan', email_key)}")
        info("Note", "tempmail.plus is stateless — any address@mailto.plus is valid")
        print()
        return

    if site == "10minutemail.net":
        mb = cache["mailboxes"].get(email_key, {})
        key  = mb.get("tenminnet_key", "")
        addr = mb.get("tenminnet_address", email_key)
        import time as _t
        created = mb.get("tenminnet_created_at", 0)
        if key and (_t.time() - created) < 540:
            dbg(f"cmd_mail_id: 10mm_net {email_key} found in cache")
            header(f"Mailbox: {addr}")
            ok(f"10minutemail.net session active: {c('cyan', addr)}")
            info("Session Key", key[:8] + "...")
            print()
            return
        info("Status", "Not in cache or expired — creating new 10minutemail.net session ...")
        try:
            address, key = tenminnet_create_session(cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        header(f"Mailbox: {address}")
        ok(f"Created: {c('cyan', address)}")
        info("Session Key", key[:8] + "...")
        info("Note", "Address is server-assigned by 10minutemail.net; session expires in ~10 min")
        print()
        return

    if site == "dropmail.me":
        mb = cache["mailboxes"].get(email_key, {})
        sid   = mb.get("dropmail_session_id", "")
        addr  = mb.get("dropmail_address", "")
        if sid and addr:
            dbg(f"cmd_mail_id: dropmail {email_key} found in cache")
            header(f"Mailbox: {addr}")
            ok(f"Dropmail session restored: {c('cyan', addr)}")
            info("Session ID", sid[:12] + "...")
            print()
            return
        info("Status", "Not in cache — creating new dropmail.me session ...")
        try:
            address = dropmail_create_session(cache, email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        p = cache["mailboxes"].get(email_key, {})
        sid = p.get("dropmail_session_id", "")
        header(f"Mailbox: {address}")
        ok(f"Created: {c('cyan', address)}")
        info("Session ID", sid[:12] + "..." if sid else "(unknown)")
        info("Note", "Address is server-assigned by dropmail.me")
        print()
        return

    if site == "harakirimail.com":
        header(f"Mailbox: {email_key}")
        ok(f"Harakirimail inbox ready: {c('cyan', email_key)}")
        info("Note", "harakirimail.com is stateless — any username@harakirimail.com is valid, emails auto-deleted after 24h")
        print()
        return

    if site == "eyepaste.com":
        email_key = f"testclaude@{EYEPASTE_DOMAIN}"
        info("Mail-ID", email_key)
        info("Note", "eyepaste.com is stateless — any username@eyepaste.com is valid, emails expire after 1h")
        return

    if site == "48hr.email":
        email_key = f"testclaude@{HR48_DOMAIN}"
        info("Mail-ID", email_key)
        info("Note", "48hr.email is stateless — any username@48hr.email is valid, emails auto-delete after 48h")
        return

    if site == "evilmail.pro":
        mb = cache["mailboxes"].get(email_key, {})
        token = mb.get("evilmail_token", "")
        addr  = mb.get("evilmail_address", "")
        if not token:
            try:
                data = evilmail_create_inbox()
                token = data["sessionToken"]
                addr  = data["email"]
                expires = data.get("expiresAt", "")
            except RuntimeError as e:
                err(str(e)); sys.exit(1)
            cache["mailboxes"][email_key] = {
                "evilmail_token":   token,
                "evilmail_address": addr,
            }
            save_cache(cache)
        header(f"Mailbox: {addr}")
        ok(f"evilmail.pro inbox ready: {c('cyan', addr)}")
        info("Note", f"Session token: {token[:16]}...")
        info("Note", "Emails auto-expire after TTL (60 min by default)")
        print()
        return


    if site == "minuteinbox.com":
        try:
            s, real_addr = minuteinbox_get_session(cache, email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        header(f"Mailbox: {email_key}")
        ok(f"minuteinbox.com inbox ready: {c('cyan', real_addr)}")
        info("Note", "Address is server-assigned by minuteinbox.com (domain: minafter.com)")
        print()
        return


    if site == "mohmal.com":
        try:
            s, email_addr = mohmal_create_session()
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        # Persist cookies so session survives process restarts
        try:
            cookies = dict(s.cookies)
        except Exception:
            cookies = {}
        cache["mailboxes"].setdefault(email_addr, {})["mohmal_cookies"] = cookies
        save_cache(cache)
        email_key = email_addr
        header(f"Mailbox: {email_key}")
        ok(f"Mohmal session created: {c('cyan', email_key)}")
        print()
        return

    if site not in LARAVEL_SITES:
        err(f"cmd_mail_id for {site} not yet implemented.")
        sys.exit(1)

        err(f"cmd_mail_id for {site} not yet implemented.")
        sys.exit(1)

    mb = cache["mailboxes"].get(email_key, {})
    if mb.get("session_cookies") and mb.get("xsrf_token") and mb.get("meta_token"):
        dbg(f"cmd_mail_id: {email_key} found in cache, validating ...")
        try:
            _tmq_get_session(email_key, cache)
            ok("Session restored from cache.")
            info("Email",       email_key)
            info("Email token", mb.get("email_token", "(unknown)"))
            print()
            return
        except Exception as e:
            warn(f"Cache restore failed ({e}), re-creating ...")

    info("Status", "Not in cache — creating session on server …")
    try:
        _tmq_get_session(email_key, cache)
    except RuntimeError as e:
        err(str(e))
        sys.exit(1)

    mb = cache["mailboxes"][email_key]
    if email_key != email_raw_key:
        cache["mailboxes"][email_raw_key] = {"redirect_to": email_key}
        save_cache(cache)
    ok(f"Created: {c('cyan', email_key)}")
    info("Email token", mb.get("email_token", "(unknown)"))
    print()


def cmd_list_message(email_raw: str, cache: dict):
    user, domain, site = parse_email(email_raw)
    email_key = f"{user}@{domain}"
    email_key = resolve_mock_id(email_key, cache)
    user, domain, site = parse_email(email_key)

    if site == "chatworkon.com":
        header(f"Messages in {email_key}")
        try:
            body = cwo_list_mails(email_key, cache)
        except RuntimeError as e:
            err(str(e))
            sys.exit(1)

        if "error" in body:
            err(f"Server error: {body['error']}")
            sys.exit(1)

        # Parse each raw message in results to build the message list
        parsed_messages = []
        for item in body.get("results", []):
            parsed = cwo_parse_raw_email(item.get("raw", ""))
            # Keep ID from the API item
            parsed["id"] = item.get("id")
            parsed_messages.append(parsed)

        cache["mailboxes"].setdefault(email_key, {})["messages"] = parsed_messages
        save_cache(cache)

        messages = parsed_messages
        if not messages:
            warn("Inbox is empty.")
            print()
            return

        print()
        for i, msg in enumerate(messages, 1):
            frm  = msg.get("from") or msg.get("from_email") or "unknown"
            subj = msg.get("subject", "(no subject)")
            date = msg.get("date") or ""
            dot  = c("dim","○") # chatworkon doesn't have read/seen status in API usually
            print(f"  {dot} {c('bold',str(i)+'.')} {c('cyan',subj)}")
            print(f"       {c('dim','From:')} {frm}   {c('dim',date)}")
            print()
        print(f"  {c('dim', str(len(messages))+' message(s) total')}")
        print()
        return

    if site == "tempmailsall.com":
        header(f"Messages in {email_key}")
        try:
            body = tms_list_mails(email_key, cache)
        except RuntimeError as e:
            err(str(e))
            sys.exit(1)

        if not body.get("success"):
            err(f"Server error: {body.get('error', 'unknown error')}")
            sys.exit(1)

        # Parse emails
        data = body.get("data", {})
        emails = data.get("emails", [])

        # Normalize into standard message schema
        parsed_messages = []
        for m in emails:
            sender = m.get("sender") or ""
            sender_name = m.get("sender_name") or ""
            frm = f"{sender_name} <{sender}>" if sender_name else sender
            
            parsed_messages.append({
                "id": m.get("id"),
                "from": frm,
                "from_email": sender,
                "subject": m.get("subject") or "(no subject)",
                "date": m.get("received_at") or "",
                "is_read": m.get("is_read", True),
            })

        cache["mailboxes"].setdefault(email_key, {})["messages"] = parsed_messages
        save_cache(cache)

        messages = parsed_messages
        if not messages:
            warn("Inbox is empty.")
            print()
            return

        print()
        for i, msg in enumerate(messages, 1):
            frm  = msg.get("from") or "unknown"
            subj = msg.get("subject", "(no subject)")
            date = msg.get("date") or ""
            read = msg.get("is_read", True)
            dot  = c("dim","○") if read else c("yellow","●")
            print(f"  {dot} {c('bold',str(i)+'.')} {c('cyan',subj)}")
            print(f"       {c('dim','From:')} {frm}   {c('dim',date)}")
            print()
        print(f"  {c('dim', str(len(messages))+' message(s) total')}")
        print()
        return

    if site == "mail.tm":
        header(f"Messages in {email_key}")
        try:
            messages = mailtm_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e))
            sys.exit(1)

        # Normalise into standard cache format
        normalised = []
        for m in messages:
            frm_obj = m.get("from", {})
            frm = frm_obj.get("name") or frm_obj.get("address") or "unknown"
            frm_addr = frm_obj.get("address", "")
            if frm_addr and frm_addr != frm:
                frm = f"{frm} <{frm_addr}>"
            normalised.append({
                "id":      m.get("id", ""),
                "from":    frm,
                "subject": m.get("subject") or "(no subject)",
                "date":    m.get("createdAt", ""),
                "is_read": m.get("seen", False),
                "intro":   m.get("intro", ""),
            })

        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty.")
            print()
            return

        print()
        for i, msg in enumerate(normalised, 1):
            dot  = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "guerrillamail.com":
        header(f"Messages in {email_key}")
        try:
            messages = guerrilla_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in messages:
            normalised.append({
                "id":      m.get("mail_id", ""),
                "from":    m.get("mail_from", "unknown"),
                "subject": m.get("mail_subject") or "(no subject)",
                "date":    m.get("mail_date", ""),
                "is_read": bool(m.get("mail_read", False)),
                "intro":   m.get("mail_exerpt", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot  = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "openinbox.io":
        header(f"Messages in {email_key}")
        try:
            messages = openinbox_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in messages:
            normalised.append({
                "id":      str(m.get("id", "")),
                "from":    m.get("from", "unknown"),
                "subject": m.get("subject") or "(no subject)",
                "date":    m.get("receivedAt", ""),
                "is_read": False,
                "body_html": m.get("html", ""),
                "body_plain": m.get("body", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "10minutemail.com":
        header(f"Messages in {email_key}")
        try:
            messages = tenminmail_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in messages:
            normalised.append({
                "id":      str(m.get("id", "")),
                "from":    m.get("sender", "unknown"),
                "subject": m.get("subject") or "(no subject)",
                "date":    m.get("sentDateFormatted", ""),
                "is_read": False,
                "body_plain": m.get("bodyPlainText", ""),
                "body_html":  m.get("bodyHtmlContent", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "mailinator.com":
        header(f"Messages in {email_key}")
        try:
            msgs = mailinator_list_messages(user)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            # time field is epoch-ms
            import datetime
            ts = m.get("time", 0)
            date_str = datetime.datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S UTC") if ts else ""
            normalised.append({
                "id":      m.get("id", ""),
                "from":    m.get("from", "unknown"),
                "subject": m.get("subject") or "(no subject)",
                "date":    date_str,
                "is_read": bool(m.get("read", False)),
                "seconds_ago": m.get("seconds_ago", 0),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "maildrop.cc":
        header(f"Messages in {email_key}")
        try:
            msgs = maildrop_list_messages(user)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            frm_raw = m.get("headerfrom") or m.get("mailfrom") or "unknown"
            normalised.append({
                "id":      m.get("id", ""),
                "from":    frm_raw,
                "subject": m.get("subject") or "(no subject)",
                "date":    m.get("date", ""),
                "is_read": False,
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "temp-mail.io":
        header(f"Messages in {email_key}")
        try:
            msgs = tempmailio_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("from_email") or m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("created_at", ""),
                "is_read":    False,
                "body_html":  m.get("body_html", ""),
                "body_plain": m.get("body_text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "freecustom.email":
        header(f"Messages in {email_key}")
        try:
            msgs = freecustom_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            frm_raw = m.get("from", "unknown")
            if isinstance(frm_raw, dict):
                frm_raw = frm_raw.get("name") or frm_raw.get("address") or frm_raw.get("email") or "unknown"
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       frm_raw,
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("date", ""),
                "is_read":    bool(m.get("read", False)),
                "body_html":  m.get("html", ""),
                "body_plain": m.get("text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "tempemail.cc":
        header(f"Messages in {email_key}")
        try:
            msgs = tempemail_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            frm_raw = m.get("from", "unknown")
            if isinstance(frm_raw, dict):
                frm_raw = frm_raw.get("name") or frm_raw.get("address") or "unknown"
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       frm_raw,
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("date", ""),
                "is_read":    bool(m.get("seen", False)),
                "body_html":  m.get("html", ""),
                "body_plain": m.get("text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return
    if site == "fakemail.net":
        header(f"Messages in {email_key}")
        try:
            msgs = fakemail_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        # fakemail fields: id, od (from), predmet (subject), kdy (date), precteno (read)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("od", "unknown"),
                "subject":    m.get("predmet") or "(no subject)",
                "date":       m.get("kdy", ""),
                "is_read":    bool(m.get("precteno", False)),
                "body_html":  "",
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "tempforward.com":
        header(f"Messages in {email_key}")
        try:
            msgs = tempforward_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            frm_addr = m.get("from_address", "")
            frm_name = m.get("from_name", "")
            frm = f"{frm_name} <{frm_addr}>" if frm_name and frm_addr else (frm_addr or frm_name or "unknown")
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       frm,
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("created_at", ""),
                "is_read":    bool(m.get("is_read", False)),
                "body_html":  "",
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "○") if msg.get("is_read") else c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return




    if site == "tempmailo.com":
        header(f"Messages in {email_key}")
        try:
            msgs = tempmailo_com_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        # fields: id, from, subject, date, text, html
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("date", ""),
                "is_read":    False,
                "body_html":  m.get("html", ""),
                "body_plain": m.get("text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("dim", "	") if msg.get("is_read") else c("yellow", "?")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "mailmomy.com":
        header(f"Messages in {email_key}")
        try:
            msgs = mailmomy_list_messages(email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)

        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("receivedAt", ""),
                "is_read":    False,
                "body_html":  m.get("message", ""),  # full body in listing
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)

        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return


    if site == "catchmail.io":
        header(f"Messages in {email_key}")
        try:
            msgs = catchmail_list_messages(email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("received_at", ""),
                "is_read":    False,
                "body_html":  m.get("body_html", ""),
                "body_plain": m.get("body_text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "10minutemail.net":
        header(f"Messages in {email_key}")
        try:
            msgs = tenminnet_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("mail_unique_id", "")),
                "from":       m.get("mail_from", "unknown"),
                "subject":    m.get("mail_subject") or "(no subject)",
                "date":       m.get("mail_date", ""),
                "is_read":    bool(m.get("mail_read", False)),
                "body_html":  "",
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "\u25cf")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        return

    if site == "dropmail.me":
        header(f"Messages in {email_key}")
        try:
            msgs = dropmail_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("fromAddr", "unknown"),
                "subject":    m.get("headerSubject") or "(no subject)",
                "date":       m.get("receivedAt", ""),
                "is_read":    False,
                "body_html":  m.get("html", ""),
                "body_plain": m.get("text", ""),
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "harakirimail.com":
        header(f"Messages in {email_key}")
        try:
            msgs = harakirimail_list_messages(email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":      m.get("_id", ""),
                "from":    m.get("from", "unknown"),
                "subject": m.get("subject") or "(no subject)",
                "date":    m.get("received", ""),
                "is_read": False,
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("No messages yet.")
            print()
            return
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "eyepaste.com":
        header(f"Messages in {email_key}")
        try:
            msgs = eyepaste_list_messages(email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("date", ""),
                "is_read":    False,
                "body_html":  m.get("body_html", ""),
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            frm  = msg.get("from", "unknown")
            subj = msg.get("subject", "(no subject)")
            date = msg.get("date", "")
            dot = c("yellow", "\u25cf")
            dim_frm = c("dim", frm[:28])
            print(f"  {dot} [{i}] {subj[:55]:<55}  {dim_frm}")
            if date:
                dim_date = c("dim", date)
                print(f"       {dim_date}")
        print()
        return

    if site == "48hr.email":
        header(f"Messages in {email_key}")
        try:
            msgs = hr48_list_messages(email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            frm = m.get("from", [])
            if isinstance(frm, list) and frm:
                frm = frm[0].get("address", "unknown")
            elif isinstance(frm, dict):
                frm = frm.get("address", "unknown")
            normalised.append({
                "id":         str(m.get("uid", "")),
                "from":       frm,
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("date", ""),
                "is_read":    False,
                "body_html":  "",
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            frm  = msg.get("from", "unknown")
            subj = msg.get("subject", "(no subject)")
            date = msg.get("date", "")
            dot = c("yellow", "\u25cf")
            dim_frm = c("dim", frm[:28])
            print(f"  {dot} [{i}] {subj[:55]:<55}  {dim_frm}")
            if date:
                dim_date = c("dim", date)
                print(f"       {dim_date}")
        print()
        return


    if site == "evilmail.pro":
        header(f"Messages in {email_key}")
        mb    = cache["mailboxes"].get(email_key, {})
        token = mb.get("evilmail_token", "")
        if not token:
            err(f"No evilmail session for {email_key}. Run --mail-id {email_key} first.")
            sys.exit(1)
        try:
            msgs, addr = evilmail_list_messages(token)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("uid", "")),
                "from":       m.get("from", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("receivedAt", ""),
                "is_read":    False,
                "body_html":  m.get("body", ""),
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            frm  = msg.get("from", "unknown")
            subj = msg.get("subject", "(no subject)")
            date = msg.get("date", "")
            dot = c("yellow", "\u25cf")
            dim_frm = c("dim", frm[:28])
            print(f"  {dot} [{i}] {subj[:55]:<55}  {dim_frm}")
            if date:
                print(f"       {c('dim', date)}")
        print()
        return


        header(f"Messages in {email_key}")
        try:
            msgs = minuteinbox_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":      str(m.get("id", "")),
                "from":    m.get("od", "unknown"),
                "subject": m.get("predmet") or "(no subject)",
                "date":    m.get("kdy", ""),
                "is_read": False,
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("No messages yet.")
            print()
            return
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return


    if site == "mohmal.com":
        header(f"Messages in {email_key}")
        try:
            msgs = mohmal_list_messages(email_key, cache)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("id", "")),
                "from":       m.get("sender", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("time", ""),
                "is_read":    False,
                "body_html":  "",
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return

    if site == "tempmail.plus":
        header(f"Messages in {email_key}")
        try:
            msgs = tempmailplus_list_messages(email_key)
        except RuntimeError as e:
            err(str(e)); sys.exit(1)
        normalised = []
        for m in msgs:
            normalised.append({
                "id":         str(m.get("mail_id", "")),
                "from":       m.get("from_mail", "unknown"),
                "subject":    m.get("subject") or "(no subject)",
                "date":       m.get("time", ""),
                "is_read":    not m.get("is_new", True),
                "body_html":  "",
                "body_plain": "",
            })
        cache["mailboxes"].setdefault(email_key, {})["messages"] = normalised
        save_cache(cache)
        if not normalised:
            warn("Inbox is empty."); print(); return
        print()
        for i, msg in enumerate(normalised, 1):
            dot = c("yellow", "●") if msg["is_read"] is False else c("dim", "○")
            print(f"  {dot} {c('bold', str(i)+'.')} {c('cyan', msg['subject'])}")
            print(f"       {c('dim','From:')} {msg['from']}   {c('dim', msg['date'])}")
            print()
        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return


    if site not in LARAVEL_SITES:
        err(f"cmd_list_message for {site} not yet implemented.")
        sys.exit(1)


    if site not in LARAVEL_SITES:
        err(f"cmd_list_message for {site} not yet implemented.")
        sys.exit(1)

    header(f"Messages in {email_key}")

    try:
        body = _tmq_call(email_key, "/get_messages", {}, cache)
    except RuntimeError as e:
        err(str(e))
        sys.exit(1)

    if "error" in body:
        err(f"Server error: {body['error']}")
        sys.exit(1)

    cache["mailboxes"][email_key]["messages"] = body.get("messages", [])
    save_cache(cache)

    messages = body.get("messages", [])
    if not messages:
        warn("Inbox is empty.")
        print()
        return

    print()
    for i, msg in enumerate(messages, 1):
        frm  = msg.get("from") or msg.get("from_email") or msg.get("from_mail", "unknown")
        subj = msg.get("subject", "(no subject)")
        date = msg.get("receivedAt") or msg.get("date") or msg.get("created_at", "")
        read = msg.get("is_seen", msg.get("read", True))
        dot  = c("yellow","●") if not read else c("dim","○")
        print(f"  {dot} {c('bold',str(i)+'.')} {c('cyan',subj)}")
        print(f"       {c('dim','From:')} {frm}   {c('dim',date)}")
        print()
    print(f"  {c('dim', str(len(messages))+' message(s) total')}")
    print()


def _strip_html(raw: str) -> str:
    # Turn <a href="URL">text</a> into "text (URL)" before stripping tags,
    # so links aren't silently lost.
    raw = re.sub(
        r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        lambda m: f"{re.sub(r'<[^>]+>', '', m.group(2)).strip()} ({m.group(1)})"
                  if re.sub(r'<[^>]+>', '', m.group(2)).strip() else f"({m.group(1)})",
        raw, flags=re.I | re.S,
    )
    raw = re.sub(r'<br\s*/?>', '\n', raw, flags=re.I)
    raw = re.sub(r'</(p|div|tr|li|h[1-6])>', '\n', raw, flags=re.I)
    raw = re.sub(r'<li[^>]*>', '  • ', raw, flags=re.I)
    raw = re.sub(r'<[^>]+>', '', raw)
    text = html.unescape(raw)
    # collapse runs of blank lines left over from nested divs
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def cmd_view_message(email_raw: str, serial: int, cache: dict):
    user, domain, site = parse_email(email_raw)
    email_key = f"{user}@{domain}"
    email_key = resolve_mock_id(email_key, cache)
    user, domain, site = parse_email(email_key)

    if site == "chatworkon.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])

        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}")
            sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from") or msg.get("from_email") or "unknown"
        frm_email = msg.get("from_email", "")
        if frm_email and frm_email != frm:
            frm = f"{frm} <{frm_email}>"
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date") or ""
        msg_id = msg.get("id", "")

        # Prefer html_body if present (will be stripped), otherwise content
        body = msg.get("html_body") or msg.get("content") or ""

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm)
        info("Subject", subj)
        info("Date",    date)
        if msg_id: info("ID", msg_id)
        print()
        print(c("dim","─"*60))
        print()

        if body:
            cleaned_body = _strip_html(body) if msg.get("html_body") else body
            for line in cleaned_body.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72):
                        print("  " + w)
                else:
                    print()
        else:
            warn("(No body content)")

        print()
        print(c("dim","─"*60))
        print()
        return

    if site == "tempmailsall.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])

        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}")
            sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from") or "unknown"
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date") or ""
        msg_id = msg.get("id", "")

        body_data = {}
        if msg_id:
            try:
                body_resp = tms_get_message(email_key, msg_id, cache)
                if body_resp.get("success"):
                    body_data = body_resp.get("data", {})
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        
        body = body_data.get("body_html") or body_data.get("body_text") or msg.get("content") or ""

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm)
        info("Subject", subj)
        info("Date",    date)
        if msg_id: info("ID", msg_id)
        print()
        print(c("dim","─"*60))
        print()

        if body:
            cleaned_body = _strip_html(body) if body_data.get("body_html") else body
            for line in cleaned_body.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72):
                        print("  " + w)
                else:
                    print()
        else:
            warn("(No body content)")

        print()
        print(c("dim","─"*60))
        print()
        return

    if site == "mail.tm":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])

        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}")
            sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")

        body = ""
        if msg_id:
            try:
                full = mailtm_get_message(email_key, msg_id, cache)
                body = full.get("html", [None])[0] if full.get("html") else ""
                if not body:
                    body = full.get("text", [None])[0] if full.get("text") else ""
                    if not body:
                        body = full.get("intro", "")
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm)
        info("Subject", subj)
        info("Date",    date)
        if msg_id: info("ID", msg_id)
        print()
        print(c("dim", "─"*60))
        print()

        if body:
            for line in _strip_html(body).splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72):
                        print("  " + w)
                else:
                    print()
        else:
            warn("(No body content)")

        print()
        print(c("dim", "─"*60))
        print()
        return

    if site == "guerrillamail.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")

        body = msg.get("body_html") or msg.get("body_plain") or msg.get("intro") or ""
        if msg_id and not body:
            try:
                full = guerrilla_get_message(email_key, msg_id, cache)
                body = full.get("mail_body", "")
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            for line in _strip_html(body).splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "openinbox.io":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")

        body = msg.get("body_html") or msg.get("body_plain") or ""
        if msg_id and not body:
            try:
                full = openinbox_get_message(email_key, msg_id, cache)
                body = full.get("html") or full.get("body") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if msg.get("body_html") else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "10minutemail.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg  = messages[serial - 1]
        frm  = msg.get("from", "unknown")
        subj = msg.get("subject", "(no subject)")
        date = msg.get("date", "")
        body = msg.get("body_html") or msg.get("body_plain") or ""

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if msg.get("body_html") else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "mailinator.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")

        body = ""
        if msg_id:
            try:
                full = mailinator_get_message(user, msg_id)
                body = mailinator_extract_body(full)
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            for line in _strip_html(body).splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "maildrop.cc":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")

        body = ""
        if msg_id:
            try:
                full = maildrop_get_message(user, msg_id)
                body = full.get("html", "")
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            for line in _strip_html(body).splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "temp-mail.io":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if msg.get("body_html") else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "freecustom.email":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        # Fetch full message from server if body not in cache
        if not body and msg_id:
            try:
                full = freecustom_get_message(email_key, msg_id, cache)
                body = full.get("html", "") or full.get("text", "")
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if msg.get("body_html") or "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "tempemail.cc":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        # Fetch full message from server if body not in cache
        if not body and msg_id:
            try:
                full = tempemail_get_message(email_key, msg_id, cache)
                body = full.get("html", "") or full.get("text", "")
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if msg.get("body_html") or "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "fakemail.net":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        # Fetch full message body from server (fakemail stores telo=HTML body)
        if not body and msg_id:
            try:
                full = fakemail_get_message(email_key, msg_id, cache)
                body = full.get("telo", "") or full.get("html", "") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return

    if site == "tempforward.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1–{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = ""

        # Always fetch full message for body (inbox listing doesn't include body)
        if msg_id:
            try:
                full = tempforward_get_message(email_key, msg_id, cache)
                # API uses html_body / text_body fields
                body = full.get("html_body", "") or full.get("text_body", "") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")

        header(f"Message #{serial}  —  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "─"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "─"*60)); print()
        return


    if site == "tempmailo.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        header(f"Message #{serial}  -  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "-"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

    if site == "mailmomy.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)

        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""

        header(f"Message #{serial}  -  {email_key}")
        info("From",    frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "-"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return
        return

    if site == "catchmail.io":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""
        if not body and msg_id:
            try:
                full = catchmail_get_message(msg_id, email_key)
                body = full.get("body_html") or full.get("body_text") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message #{serial}  -  {email_key}")
        info("From", frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "-"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

    if site == "10minutemail.net":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_plain", "") or msg.get("body_html", "")
        if not body and msg_id:
            try:
                full = tenminnet_get_message(email_key, msg_id, cache)
                if full:
                    body = full.get("body_plain", "") or full.get("body_html", "") or str(full)
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message {serial} of {len(messages)}")
        print(f"  {c('dim','From:')}    {frm}")
        print(f"  {c('dim','Subject:')} {subj}")
        print(f"  {c('dim','Date:')}    {date}")
        print()
        if body:
            import html, textwrap
            cleaned = html.unescape(body)
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

    if site == "dropmail.me":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_plain", "") or msg.get("body_html", "")
        if not body and msg_id:
            try:
                full = dropmail_get_message(email_key, msg_id, cache)
                body = full.get("text", "") or full.get("html", "")
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message {serial} of {len(messages)}")
        print(f"  {c('dim','From:')}    {frm}")
        print(f"  {c('dim','Subject:')} {subj}")
        print(f"  {c('dim','Date:')}    {date}")
        print()
        if body:
            import html, textwrap
            cleaned = html.unescape(body)
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

    if site == "harakirimail.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_plain", "") or msg.get("body_html", "")
        if not body and msg_id:
            try:
                full = harakirimail_get_message(msg_id)
                body = full.get("bodytext", "") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message {serial} of {len(messages)}")
        print(f"  {c('dim','From:')}    {frm}")
        print(f"  {c('dim','Subject:')} {subj}")
        print(f"  {c('dim','Date:')}    {date}")
        print()
        if body:
            import html, textwrap
            cleaned = html.unescape(body)
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

        return

    if site == "eyepaste.com":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            # Re-fetch if cache empty
            try:
                msgs = eyepaste_list_messages(email_key)
            except Exception as e:
                err(str(e)); sys.exit(1)
            messages = msgs
        if not messages:
            warn("Inbox is empty."); return
        if serial < 1 or serial > len(messages):
            err(f"Message #{serial} not found (inbox has {len(messages)} messages)."); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        body   = msg.get("body_html", "")
        import html, textwrap
        header(f"Message #{serial} in {email_key}")
        print(f"  From:    {frm}")
        print(f"  Subject: {subj}")
        print(f"  Date:    {date}")
        print()
        cleaned = _strip_html(body) if "<" in body else body
        for line in cleaned.splitlines():
            if line.strip():
                for w in textwrap.wrap(line, width=72): print("  " + w)
            else:
                print()
        return

    if site == "48hr.email":
        try:
            msgs = hr48_list_messages(email_key)
        except Exception as e:
            err(str(e)); sys.exit(1)
        if not msgs:
            warn("Inbox is empty."); return
        if serial < 1 or serial > len(msgs):
            err(f"Message #{serial} not found (inbox has {len(msgs)} messages)."); sys.exit(1)
        m   = msgs[serial - 1]
        uid = m.get("uid")
        try:
            full = hr48_get_message(email_key, uid)
        except Exception as e:
            err(str(e)); sys.exit(1)
        frm  = full.get("from", {})
        if isinstance(frm, list) and frm:
            frm = frm[0].get("address", "unknown")
        elif isinstance(frm, dict):
            frm = frm.get("text", frm.get("address", "unknown"))
        subj = full.get("subject", "(no subject)")
        date = full.get("date", "")
        body = full.get("text") or full.get("html") or "(no body)"
        import textwrap
        header(f"Message #{serial} in {email_key}")
        print(f"  From:    {frm}")
        print(f"  Subject: {subj}")
        print(f"  Date:    {date}")
        print()
        cleaned = _strip_html(body) if "<" in body else body
        for line in cleaned.splitlines():
            if line.strip():
                for w in textwrap.wrap(line, width=72): print("  " + w)
            else:
                print()
        return


    if site == "evilmail.pro":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg  = messages[serial - 1]
        frm  = msg.get("from", "unknown")
        subj = msg.get("subject", "(no subject)")
        date = msg.get("date", "")
        body = msg.get("body_html", "") or msg.get("body_plain", "")
        import textwrap
        header(f"Message #{serial} in {email_key}")
        print(f"  From:    {frm}")
        print(f"  Subject: {subj}")
        print(f"  Date:    {date}")
        print()
        cleaned = _strip_html(body) if "<" in body else body
        for line in cleaned.splitlines():
            if line.strip():
                for w in textwrap.wrap(line, width=72): print("  " + w)
            else:
                print()
        return


        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_plain", "") or msg.get("body_html", "")
        if not body and msg_id:
            try:
                body = minuteinbox_get_message(email_key, msg_id, cache)
                # response is HTML string
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message {serial} of {len(messages)}")
        print(f"  {c('dim','From:')}    {frm}")
        print(f"  {c('dim','Subject:')} {subj}")
        print(f"  {c('dim','Date:')}    {date}")
        print()
        if body:
            import html, textwrap
            cleaned = html.unescape(body)
            # strip basic HTML tags for plain display
            import re as _re
            cleaned = _re.sub(r'<[^>]+>', ' ', cleaned)
            cleaned = cleaned.strip()
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""
        if not body and msg_id:
            try:
                full = mohmal_get_message(email_key, msg_id, cache)
                body = full.get("body_html") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message #{serial}  -  {email_key}")
        info("From", frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "-"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return

    if site == "tempmail.plus":
        mb       = cache["mailboxes"].get(email_key, {})
        messages = mb.get("messages", [])
        if not messages:
            warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
            sys.exit(1)
        if serial < 1 or serial > len(messages):
            err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
        msg    = messages[serial - 1]
        frm    = msg.get("from", "unknown")
        subj   = msg.get("subject", "(no subject)")
        date   = msg.get("date", "")
        msg_id = msg.get("id", "")
        body   = msg.get("body_html") or msg.get("body_plain") or ""
        if not body and msg_id:
            try:
                full = tempmailplus_get_message(email_key, msg_id)
                body = full.get("html") or full.get("text") or ""
            except Exception as e:
                warn(f"Could not fetch message body ({e})")
        header(f"Message #{serial}  -  {email_key}")
        info("From", frm); info("Subject", subj); info("Date", date)
        if msg_id: info("ID", msg_id)
        print(); print(c("dim", "-"*60)); print()
        if body:
            cleaned = _strip_html(body) if "<" in body else body
            for line in cleaned.splitlines():
                if line.strip():
                    for w in textwrap.wrap(line, width=72): print("  " + w)
                else: print()
        else:
            warn("(No body content)")
        print(); print(c("dim", "-"*60)); print()
        return


    mb       = cache["mailboxes"].get(email_key, {})
    messages = mb.get("messages", [])

    if not messages:
        warn(f"No messages in cache for {email_key}. Run --list-message {email_key} first.")
        sys.exit(1)
    if serial < 1 or serial > len(messages):
        err(f"Invalid number. Valid range: 1–{len(messages)}")
        sys.exit(1)

    msg    = messages[serial - 1]
    frm    = msg.get("from") or msg.get("from_email") or msg.get("from_mail", "unknown")
    frm_email = msg.get("from_email", "")
    if frm_email and frm_email != frm:
        frm = f"{frm} <{frm_email}>"
    subj   = msg.get("subject", "(no subject)")
    date   = msg.get("receivedAt") or msg.get("date") or msg.get("created_at", "")
    msg_id = msg.get("id", "")

    # /get_messages always returns content:"" — the real body lives at GET /msg/{id}
    # (the site loads it into a sandboxed iframe on its /view/{id} page).
    body = ""
    if msg_id:
        try:
            body = _tmq_fetch_message_html(email_key, msg_id, cache)
        except Exception as e:
            warn(f"Could not fetch message body ({e})")
    if not body:
        body = msg.get("content") or msg.get("body") or msg.get("html_body") or msg.get("text_body", "")

    header(f"Message #{serial}  —  {email_key}")
    info("From",    frm)
    info("Subject", subj)
    info("Date",    date)
    if msg_id: info("ID", msg_id)
    print()
    print(c("dim","─"*60))
    print()

    if body:
        for line in _strip_html(body).splitlines():
            if line.strip():
                for w in textwrap.wrap(line, width=72):
                    print("  " + w)
            else:
                print()
    else:
        warn("(No body content)")

    print()
    print(c("dim","─"*60))
    print()


def cmd_delete_id(email_raw: str, cache: dict):
    user, domain, site = parse_email(email_raw)
    email_key = f"{user}@{domain}"

    # Check if this input is a mock ID redirecting to a real ID
    mb = cache.get("mailboxes", {}).get(email_key, {})
    mock_key = None
    if isinstance(mb, dict) and "redirect_to" in mb:
        mock_key = email_key
        email_key = mb["redirect_to"]
        user, domain, site = parse_email(email_key)

    if site == "chatworkon.com":
        header(f"Delete: {email_key}")
        if email_key not in cache["mailboxes"]:
            warn(f"'{email_key}' not found in local cache.")
            print()
            return
        cwo_delete_local(email_key, cache)
        ok(f"Removed '{email_key}' from local cache.")
        if mock_key and mock_key in cache["mailboxes"]:
            del cache["mailboxes"][mock_key]
            save_cache(cache)
            ok(f"Removed mock mapping '{mock_key}' from local cache.")
        print()
        return

    if site == "tempmailsall.com":
        header(f"Delete: {email_key}")
        if email_key not in cache["mailboxes"]:
            warn(f"'{email_key}' not found in local cache.")
            print()
            return
        tms_delete_mailbox(email_key, cache)
        ok(f"Removed '{email_key}' from local cache.")
        if mock_key and mock_key in cache["mailboxes"]:
            del cache["mailboxes"][mock_key]
            save_cache(cache)
            ok(f"Removed mock mapping '{mock_key}' from local cache.")
        print()
        return

    if site == "mail.tm":
        header(f"Delete: {email_key}")
        if email_key not in cache["mailboxes"]:
            warn(f"'{email_key}' not found in local cache.")
            print()
            return
        try:
            mailtm_delete_account(email_key, cache)
            ok(f"Deleted account on mail.tm and removed from local cache.")
        except Exception as e:
            warn(f"Server delete failed ({e}) — removing from local cache anyway.")
            if email_key in cache["mailboxes"]:
                del cache["mailboxes"][email_key]
            save_cache(cache)
        print()
        return

    if site == "guerrillamail.com":
        header(f"Delete: {email_key}")
        guerrilla_delete_account(email_key, cache)
        ok(f"Removed '{email_key}' from local cache.")
        print()
        return

    if site == "openinbox.io":
        header(f"Delete: {email_key}")
        try:
            openinbox_delete_inbox(email_key, cache)
            ok(f"Removed '{email_key}' from server and local cache.")
        except Exception as e:
            warn(f"Server delete failed ({e}) — removing from local cache anyway.")
            if email_key in cache["mailboxes"]:
                del cache["mailboxes"][email_key]
            save_cache(cache)
        print()
        return

    if site == "10minutemail.com":
        header(f"Delete: {email_key}")
        tenminmail_delete_account(email_key, cache)
        ok(f"Removed '{email_key}' from local cache.")
        print()
        return

    if site == "mailinator.com":
        # Stateless — just clear local cache, nothing on server to delete
        header(f"Delete: {email_key}")
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Removed '{email_key}' from local cache (mailinator is public, no server deletion needed).")
        print()
        return

    if site == "maildrop.cc":
        # Can delete individual messages, but no full-inbox deletion
        header(f"Delete: {email_key}")
        mb = cache.get("mailboxes", {}).get(email_key, {})
        messages = mb.get("messages", [])
        deleted = 0
        for msg in messages:
            msg_id = msg.get("id", "")
            if msg_id:
                if maildrop_delete_message(user, msg_id):
                    deleted += 1
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return

    if site == "temp-mail.io":
        header(f"Delete: {email_key}")
        mb = cache.get("mailboxes", {}).get(email_key, {})
        address = mb.get("tempmailio_address", email_key)
        # Delete messages on server
        msgs = mb.get("messages", [])
        deleted = 0
        for msg in msgs:
            msg_id = msg.get("id", "")
            if msg_id:
                if tempmailio_delete_message(email_key, msg_id, cache):
                    deleted += 1
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return

    if site == "freecustom.email":
        # Stateless — just clear local cache (no server-side inbox to delete)
        header(f"Delete: {email_key}")
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Removed '{email_key}' from local cache (freecustom.email is stateless).")
        print()
        return

    if site == "tempemail.cc":
        header(f"Delete: {email_key}")
        mb   = cache.get("mailboxes", {}).get(email_key, {})
        msgs = mb.get("messages", [])
        deleted = 0
        for msg in msgs:
            msg_id = msg.get("id", "")
            if msg_id:
                if tempemail_delete_message(email_key, msg_id, cache):
                    deleted += 1
        tempemail_delete_account(email_key, cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return

    if site == "fakemail.net":
        header(f"Delete: {email_key}")
        mb   = cache.get("mailboxes", {}).get(email_key, {})
        msgs = mb.get("messages", [])
        deleted = 0
        for msg in msgs:
            msg_id = msg.get("id", "")
            if msg_id:
                try:
                    fakemail_delete_message(email_key, msg_id, cache)
                    deleted += 1
                except Exception:
                    pass
        fakemail_delete_account(email_key, cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return

    if site == "tempforward.com":
        header(f"Delete: {email_key}")
        tempforward_delete_account(email_key, cache)
        ok(f"Removed '{email_key}' from local cache.")
        print()
        return



    if site == "tempmailo.com":
        header(f"Delete: {email_key}")
        tempmailo_com_delete_account(email_key, cache)
        ok(f"Removed '{email_key}' from local cache (no server-side delete endpoint).")
        print()
        return

    if site == "mailmomy.com":
        # Delete all messages for this address on server, then clear cache
        header(f"Delete: {email_key}")
        try:
            deleted = mailmomy_delete_all(email_key)
        except Exception as e:
            warn(f"Server delete failed ({e}) — clearing local cache anyway.")
            deleted = 0
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return
        return

    if site == "catchmail.io":
        header(f"Delete: {email_key}")
        mb   = cache.get("mailboxes", {}).get(email_key, {})
        msgs = mb.get("messages", [])
        deleted = 0
        for msg in msgs:
            msg_id = msg.get("id", "")
            if msg_id:
                try:
                    catchmail_delete_message(msg_id)
                    deleted += 1
                except Exception:
                    pass
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return

    if site == "10minutemail.net":
        header(f"Delete: {email_key}")
        tenminnet_delete_session(email_key, cache)
        ok(f"10minutemail.net session cleared for '{email_key}' (no server-side delete).")
        print()
        return

    if site == "dropmail.me":
        header(f"Delete: {email_key}")
        dropmail_delete_session(email_key, cache)
        ok(f"Dropmail session cleared for '{email_key}' (no server-side delete endpoint).")
        print()
        return

    if site == "harakirimail.com":
        header(f"Delete: {email_key}")
        info("Note", "harakirimail.com auto-deletes all emails after 24h — no manual delete supported")
        cache.get("mailboxes", {}).pop(email_key, None)
        save_cache(cache)
        ok("Local cache cleared for this inbox.")
        print()
        return

    if site == "eyepaste.com":
        info("Note", "eyepaste.com auto-expires all emails after 1h — no manual delete supported")
        return

    if site == "48hr.email":
        info("Note", "48hr.email auto-deletes all emails after 48h — no manual delete supported via CLI")
        return

    if site == "evilmail.pro":
        header(f"Delete: {email_key}")
        if email_key in cache.get("mailboxes", {}):
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"evilmail.pro session cleared for '{email_key}' (emails auto-expire server-side).")
        print()
        return


    if site == "minuteinbox.com":
        header(f"Delete: {email_key}")
        mb       = cache.get("mailboxes", {}).get(email_key, {})
        messages = mb.get("messages", [])
        if serial is None:
            # Delete all (clear local cache + session)
            cache.get("mailboxes", {}).pop(email_key, None)
            save_cache(cache)
            ok("minuteinbox.com local cache cleared (session expired server-side too).")
        else:
            if serial < 1 or serial > len(messages):
                err(f"Invalid number. Valid range: 1-{len(messages)}"); sys.exit(1)
            msg_id = messages[serial - 1].get("id", "")
            try:
                minuteinbox_delete_message(email_key, msg_id, cache)
                messages.pop(serial - 1)
                cache["mailboxes"][email_key]["messages"] = messages
                save_cache(cache)
                ok(f"Message {serial} deleted.")
            except Exception as e:
                warn(f"Delete failed ({e})")
        print()
        return


    if site == "mohmal.com":
        header(f"Delete: {email_key}")
        try:
            mohmal_delete_session(email_key, cache)
        except Exception as e:
            warn(f"Server logout failed ({e}) — clearing local cache anyway.")
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Mohmal session deleted and local cache cleared for '{email_key}'.")
        print()
        return

    if site == "tempmail.plus":
        header(f"Delete: {email_key}")
        mb   = cache.get("mailboxes", {}).get(email_key, {})
        msgs = mb.get("messages", [])
        deleted = 0
        for msg in msgs:
            msg_id = msg.get("id", "")
            if msg_id:
                try:
                    tempmailplus_delete_message(email_key, msg_id)
                    deleted += 1
                except Exception:
                    pass
        if email_key in cache["mailboxes"]:
            del cache["mailboxes"][email_key]
            save_cache(cache)
        ok(f"Deleted {deleted} message(s) on server and cleared local cache for '{email_key}'.")
        print()
        return


    if site not in LARAVEL_SITES:
        err(f"cmd_delete_id for {site} not yet implemented.")
        sys.exit(1)


    header(f"Delete: {email_key}")

    if email_key not in cache["mailboxes"]:
        warn(f"'{email_key}' not found in local cache.")
        print()
        return

    try:
        body = _tmq_call(email_key, "/delete", {}, cache)
        if "error" in body:
            warn(f"Server: {body['error']} — removing from local cache anyway.")
        else:
            ok("Deleted on server.")
    except Exception as e:
        warn(f"Server call failed ({e}) — removing from local cache anyway.")

    _tmq_pool.pop(email_key, None)
    if email_key in cache["mailboxes"]:
        del cache["mailboxes"][email_key]
    if mock_key and mock_key in cache["mailboxes"]:
        del cache["mailboxes"][mock_key]
    save_cache(cache)
    ok(f"Removed '{email_key}' from local cache.")
    print()


def cmd_real_mail_id(email_raw: str, cache: dict):
    user, domain, site = parse_email(email_raw)
    email_key = f"{user}@{domain}"
    mb = cache.get("mailboxes", {}).get(email_key, {})
    if isinstance(mb, dict) and "redirect_to" in mb:
        print(mb["redirect_to"])
    else:
        print(email_key)
