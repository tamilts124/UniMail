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

    if site not in ("tempmailq.com", "maildax.cc", "dakbox.net", "temp-mail-world.com", "disposableemailgenerator.com"):
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

    if site not in ("tempmailq.com", "maildax.cc", "dakbox.net", "temp-mail-world.com", "disposableemailgenerator.com"):
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

    if site not in ("tempmailq.com", "maildax.cc", "dakbox.net", "temp-mail-world.com", "disposableemailgenerator.com"):
        err(f"cmd_view_message for {site} not yet implemented.")
        sys.exit(1)

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

    if site not in ("tempmailq.com", "maildax.cc", "dakbox.net", "temp-mail-world.com", "disposableemailgenerator.com"):
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
