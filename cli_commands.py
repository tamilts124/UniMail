#!/usr/bin/env python3
"""
cli_commands.py - all --flag command implementations for the unimail.py CLI.
"""

import sys, re, textwrap, html

from cli_config import (
    c, header, info, warn, err, ok, dbg,
    SITE_DOMAINS, DOMAIN_MAP, TEMPMAILQ_BASE, MAILDAX_BASE,
    HTTP_TIMEOUT, parse_email, save_cache,
)
from cli_tmq import (
    _tmq_new_session, _tmq_get_session, _tmq_call, _tmq_pool, _tmq_fetch_message_html,
)
from cli_maildax import maildax_fetch_csrf


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
        base = TEMPMAILQ_BASE if site == "tempmailq.com" else MAILDAX_BASE
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
    user, domain, site = parse_email(email_raw)
    email_key = f"{user}@{domain}"

    header(f"Mailbox: {email_key}")

    if site != "tempmailq.com":
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
    ok(f"Created: {c('cyan', email_key)}")
    info("Email token", mb.get("email_token", "(unknown)"))
    print()


def cmd_list_message(email_raw: str, cache: dict):
    user, domain, site = parse_email(email_raw)
    email_key = f"{user}@{domain}"

    if site != "tempmailq.com":
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

    if site != "tempmailq.com":
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

    if site != "tempmailq.com":
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
    del cache["mailboxes"][email_key]
    save_cache(cache)
    ok(f"Removed '{email_key}' from local cache.")
    print()
