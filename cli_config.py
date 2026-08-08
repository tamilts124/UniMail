#!/usr/bin/env python3
"""
cli_config.py - shared config, ANSI helpers, cache I/O, and email parsing
for the unimail.py CLI.

Split out of the original monolithic unimail.py so each concern
(config/ansi/cache, tempmailq client, maildax client, commands, entry point)
can be edited independently.
"""

import sys, os, json, time

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

CACHE_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".unimail_cache.json")
IMPERSONATE  = "chrome124"
HTTP_TIMEOUT = 20

# Sites with slower servers get a longer timeout (seconds)
SITE_TIMEOUTS = {
    "zhimail.xyz": 45,
}

DEBUG = os.environ.get("UNIMAIL_DEBUG", "0") == "1"

def set_debug(value: bool):
    """Toggle debug output at runtime (used by --debug CLI flag)."""
    global DEBUG
    DEBUG = value

def dbg(msg):
    if DEBUG:
        print(f"[{time.strftime('%H:%M:%S')}] DEBUG: {msg}", file=sys.stderr, flush=True)

SITE_DOMAINS = {
    "tempmailq.com":  ["wqacmjaqe.xyz"],
    "maildax.cc":     ["maildax.space", "maildax.store", "maildax.online"],
    "chatworkon.com": ["chatcloud.site"],
    "tempmailsall.com": ["edubd.edu.pl"],
    "dakbox.net":      ["dakbox.net"],
    "temp-mail-world.com": ["10-minutes.email"],
    "disposableemailgenerator.com": ["disposableemailgenerator.com", "hdhub4u.us"],
    # â”€â”€ New Laravel-pattern sites (HAR captured 2026-07-19) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # All share identical endpoints to tempmailq.com: /get_messages /change /delete /msg/{id}
    "temporarymailservice.com": ["tomail.fyi"],
    "zhimail.xyz": ["zhimail.xyz", "zhimail.in", "zhimails.work", "zhimails.vip"],
    "mailditch.com": ["ditch.my.id"],
    "tempmaili.com": ["munik.edu.pl"],
    # â”€â”€ mail.tm â€” public REST API, no CSRF, Bearer JWT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Domains are fetched live from /domains; seed list here for offline use.
    "mail.tm": ["emalupe.com"],  # seed domain — rotates; fetched live from /domains
    # â”€â”€ guerrillamail.com â€” public JSON API, sid_token session â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    "guerrillamail.com": [
        "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
        "guerrillamail.de", "guerrillamail.biz", "guerrillamail.info",
        "grr.la", "sharklasers.com", "spam4.me", "guerrillamailblock.com",
    ],
    # â”€â”€ 10minutemail.com â€” REST/JSON cookie-session (JSESSIONID) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Email address assigned by server; cannot be chosen. Domains are server-assigned.
    "10minutemail.com": ["vtmpj.com", "jbsze.net", "jbsze.com", "onldm.net", "gonrr.net"],
    # â”€â”€ 10minutemail.net â€” REST/JSON key-based session (no cookies)
    "10minutemail.net": ["laoia.com"],
    # â”€â”€ openinbox.io â€” clean REST API, no auth, inbox id stored in cache â”€â”€â”€â”€
    # Email address assigned by server on POST /api/inbox.
    "openinbox.io": ["inboxly.website", "inboxfast.space", "inboxfly.space"],
    # â”€â”€ mailinator.com â€” public REST API, no auth, any username works â”€â”€â”€â”€â”€â”€â”€â”€
    # GET /api/v2/domains/mailinator.com/inboxes/<inbox> â€” no key needed for public inboxes.
    "mailinator.com": ["mailinator.com"],
    # â”€â”€ maildrop.cc â€” public GraphQL API, no auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # POST https://api.maildrop.cc/graphql â€” { inbox(mailbox: "...") { ... } }
    "maildrop.cc": ["maildrop.cc"],
    # â”€â”€ temp-mail.io â€” internal REST API, no auth, address server-assigned â”€â”€â”€
    # POST https://api.internal.temp-mail.io/api/v3/email/new â†’ {email, token}
    # GET  https://api.internal.temp-mail.io/api/v3/email/<address>/messages â†’ []
    # Domain observed: lnovic.com (may rotate; add new ones as discovered).
    "temp-mail.io": ["lnovic.com", "bwmyga.com", "yzcalo.com"],
    # â”€â”€ freecustom.email â€” anonymous JWT, x-fce-client header required â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # POST /api/auth (no body) â†’ {token}  â€” 1-hour anonymous JWT
    # GET  /api/public-mailbox?fullMailboxId=EMAIL â†’ {success, data: [...msgs]}
    # GET  /api/public-mailbox?fullMailboxId=EMAIL&messageId=ID â†’ full message
    # Stateless: any username@domain works, no account creation needed.
    "freecustom.email": [
        "ditapi.info", "ditcloud.info", "ditdrive.info", "ditgame.info",
        "ditlearn.info", "ditpay.info", "ditplay.info", "ditube.info",
        "junkstopper.info", "areueally.info", "sqlcompiler.info",
        "addmy.space", "attachmy.site", "nimbusreach.info", "lumenbay.info",
        "haloforge.online", "haloforge.info", "echoharbor.in",
    ],
    # â”€â”€ fakemail.net â€” PHP session + AJAX endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # GET  / â†’ PHPSESSID + CSRF scraped from HTML; address server-assigned
    # GET  /index/refresh â†’ message list  POST /index/email â†’ full msg
    # Domain observed: forliion.com (may rotate)
    "fakemail.net": ["forliion.com"],
    # â”€â”€ tempemail.cc â€” internal REST API, Bearer JWT, address server-assigned â”€
    # POST https://www.tempemail.cc/api/accounts â†’ {code, data: {email, password, token, ...}}
    # GET  https://www.tempemail.cc/api/messages?limit=50 â†’ {code, data: {items: [...]}}
    # Domain observed: icmans.com (may add more as discovered).
    "tempemail.cc": ["icmans.com"],
    # â”€â”€ tempforward.com â€” token-based REST API, address server-assigned â”€â”€â”€â”€â”€â”€â”€
    # POST /api/tempmail/create â†’ {success, mailbox: {address, token, expires_at}}
    # GET  /api/tempmail/inbox?token=<token> â†’ {mailbox, emails: [...], count}
    # GET  /api/tempmail/email/<id>?token=<token> â†’ full email
    # POST /api/tempmail/extend  body:{token} â†’ extend mailbox lifetime
    "tempforward.com": ["tempforward.com"],
    # â”€â”€ tempmailo.com â€” ASP.NET Core + Cloudflare, address server-assigned â”€â”€â”€â”€
    # GET  / â†’ scrape __RequestVerificationToken hidden field; sets antiforgery + cf_clearance cookies
    # GET  /changemail?_r=<rand> (header: RequestVerificationToken) â†’ plain-text assigned email
    # GET  /changemail?tmail=<email>&_r=<rand> â†’ confirm/restore existing address
    # POST / (header: RequestVerificationToken, body JSON {mail:<email>}) â†’ messages[]
    # Domains rotate; denipl.net and fxzig.com observed 2026-07-19.
    "tempmailo.com": ["denipl.net", "denipl.com", "fxzig.com"],
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
    # -- tempmail.lol -- GEO-BLOCKED for IN (India) on free tier -----------------
    # Returns 403: "country IN not allowed to use API free tier due to abuse"
    # Requires TempMail Plus/Ultra paid subscription to bypass. Skipped.

    # -- 1secmail.com -- GEO-BLOCKED 403 from IN even with curl_cffi ------------
    # All API endpoints return 403 Forbidden from India regardless of headers.
    # Skipped â€” may work via proxy or non-IN IP.


    # -- mailmomy.com -- fully stateless open REST API, no auth -----------------
    # GET /api/domains -> [{domain, active, ...}] â€” live domain list
    # GET /api/mail/messages?to=EMAIL&page=1&limit=50 -> {emails:[...]}
    # DELETE /api/mail/delete?to=EMAIL -> {deleted: N}
    # DELETE /api/mail/delete?id=MSG_ID -> {deleted: N}
    # VERIFIED working 2026-07-19; 20 active domains; plain requests (no cffi)
    "mailmomy.com": [
        "mailmomy.com",
        "2famail.com",
        "xikemail.com",
        "protect.support",
        "easyme.pro",
        "282mail.com",
        "bsdu32.buzz",
        "nuxh62.space",
        "doxu243.buzz",
        "xue32.buzz",
        "evergreenco.shop",
        "mingyuekeji.online",
    ],
    # -- catchmail.io -- fully stateless open REST API, no auth ----------------
    # GET /api/v1/mailbox?address=EMAIL -> {messages:[{id,from,to,subject,...}]}
    # GET /api/v1/message/{id}?mailbox=EMAIL -> full message
    # DELETE /api/v1/message/{id} -> 200/204
    "catchmail.io": [
        "catchmail.io",
    ],
    # -- tempmail.plus -- stateless REST API, user-chosen address ---------------
    # GET /api/mails?email=USER@mailto.plus&first_id=0&epin= -> {mail_list:[...]}
    # GET /api/mail/{id}?email=...&epin= -> full message
    # DELETE /api/mail/{id}?email=...&epin= -> {result: true}
    "tempmail.plus": [
        "mailto.plus",
    ],
    # -- mohmal.com -- server-side HTML, HttpOnly cookie session ---------------
    # GET /en/create/random -> redirects to /en/inbox with assigned email
    # GET /en/refresh -> HTML inbox table with <tr data-msg-id="ID">
    # GET /en/message/<id> -> raw HTML body of message
    # GET /en/logout -> delete session
    # Domain observed: emailinbo.live (may rotate)
    "mohmal.com": [
        "emailinbo.live",
    ],
    # -- harakirimail.com -- public REST API, stateless, no auth -----------------
    # GET /api/v1/inbox/<username> -> {emails:[{_id,received,subject,from,spam}]}
    # GET /api/v1/email/<_id>     -> {_id,from,to,subject,bodytext,received,...}
    # No delete endpoint â€” emails auto-deleted after 24h
    "harakirimail.com": [
        "harakirimail.com",
    ],
    # -- minuteinbox.com -- PHP session, server-assigned address ----------------
    # POST /index/index  -> {"email":"user@minafter.com"}
    # GET  /index/refresh -> [{id,predmet,od,kdy,...}]
    # GET  /index/email?id=X -> HTML body
    # POST /delete-email/ id=X -> "ok"
    "minuteinbox.com": [
        "minafter.com",
    ],

    # -- dropmail.me -- GraphQL API, website token in URL path, session-based ---
    # POST /api/graphql/<token>  mutation{introduceSession{id,expiresAt,addresses{address}}}
    # POST /api/graphql/<token>  {session(id:"<id>"){addresses{address,mails{...}}}}
    # Token: website_<date+16chars>_<fnv1a(random_part+secret)>
    # Secret from <meta name="csrf-token">: "tm_graphql_secret_2026"
    # Domains (17 observed): spymail.one, pickmail.org, emlhub.com, emlpro.com,
    #   emltmp.com, freeml.net, mail2me.co, mailpwr.com, mailtowin.com, maximail.vip,
    #   mimimail.me, pickmemail.com, dropmail.me, 10mail.info, 10mail.org, 10mail.xyz, yomail.info
    "dropmail.me": [
        "spymail.one", "pickmail.org", "emlhub.com", "emlpro.com", "emltmp.com",
        "freeml.net", "mail2me.co", "mailpwr.com", "mailtowin.com", "maximail.vip",
        "mimimail.me", "pickmemail.com", "dropmail.me",
        "10mail.info", "10mail.org", "10mail.xyz", "yomail.info",
    ],

    # -- eyepaste.com -- RSS-based stateless inbox, no auth, Gmail-deliverable --
    # GET /inbox/<email>.rss -> RSS XML with <item> per message
    # Full body embedded in <description> CDATA; no delete endpoint; 1hr expiry
    "eyepaste.com": [
        "eyepaste.com",
    ],

    # -- 48hr.email -- internal REST API, stateless, no auth, Gmail-deliverable -
    # GET /api/v1/inbox/<full-email> -> list messages
    # GET /api/v1/inbox/<full-email>/<uid> -> full message; no delete via CLI
    "48hr.email": [
        "48hr.email",
    ],

    # -- evilmail.pro -- REST API, session-based token, no API key needed -------
    # POST /api/temp-email  body:{domain,ttlMinutes} -> {email, sessionToken, expiresAt}
    # GET  /api/temp-email/<sessionToken>            -> {email, messages:[{uid,from,subject,body,receivedAt}]}
    # Domain free tier: evilbx.com (domain list requires API key)
    # Emails auto-expire after TTL (60 min default)
    "evilmail.pro": [
        "evilbx.com",
    ],
}







def _build_domain_map() -> dict[str, str]:
    m = {}
    for site, domains in SITE_DOMAINS.items():
        for d in domains:
            m[d] = site
    return m

DOMAIN_MAP = _build_domain_map()

# â”€â”€ Base URLs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TEMPMAILQ_BASE  = "https://tempmailq.com"
MAILDAX_BASE    = "https://maildax.cc"
CHATWORKON_BASE     = "https://mail.chatworkon.com"
CHATWORKON_API_BASE = "https://mailapi.chatworkon.com"
TEMPMAILSALL_BASE = "https://tempmailsall.com"
DAKBOX_BASE       = "https://www.dakbox.net"
TEMPMAILWORLD_BASE = "https://www.temp-mail-world.com"
DISPOSABLE_BASE    = "https://disposableemailgenerator.com"
# New Laravel-pattern sites
TEMPORARYMAILSERVICE_BASE = "https://temporarymailservice.com"
ZHIMAIL_BASE              = "https://zhimail.xyz"
MAILDITCH_BASE            = "https://mailditch.com"
TEMPMAILI_BASE            = "https://tempmaili.com"
# mail.tm REST API
MAILTM_BASE = "https://mail.tm"
# guerrillamail.com public JSON API
GUERRILLA_BASE = "https://www.guerrillamail.com"
# 10minutemail.com cookie-session REST API
TENMINMAIL_BASE = "https://10minutemail.com"
# openinbox.io clean REST API
OPENINBOX_BASE = "https://openinbox.io"
# mailinator.com public REST API
MAILINATOR_BASE = "https://www.mailinator.com"
# maildrop.cc public GraphQL API
MAILDROP_BASE = "https://maildrop.cc"
# temp-mail.io internal REST API (address server-assigned)
TEMPMAILIO_BASE = "https://temp-mail.io"
# fakemail.net PHP session + AJAX endpoints
FAKEMAIL_BASE = "https://www.fakemail.net"
# freecustom.email anonymous JWT REST API
FREECUSTOM_BASE = "https://www.freecustom.email"
# tempemail.cc internal REST API (Bearer JWT, address server-assigned)
TEMPEMAIL_BASE = "https://www.tempemail.cc"
# tempforward.com token-based REST API (address server-assigned)
TEMPFORWARD_BASE = "https://tempforward.com"
# tempmailo.com ASP.NET Core + Cloudflare (address server-assigned)
TEMPMAILO_COM_BASE = "https://tempmailo.com"
# 1secmail.com public REST API (fully stateless, no auth)
ONESECMAIL_BASE = "https://www.1secmail.com/api/v1/"
# tempmail.lol public REST API v2 (free tier, no API key needed)
TEMPMAIL_LOL_BASE = "https://api.tempmail.lol"
# catchmail.io public REST API (fully stateless, no auth)
CATCHMAIL_BASE = "https://catchmail.io"
# tempmail.plus stateless REST API (user-chosen address, domain: mailto.plus)
TEMPMAILPLUS_BASE = "https://tempmail.plus"
# mohmal.com server-side HTML, HttpOnly cookie session
MOHMAL_BASE = "https://www.mohmal.com"
# dropmail.me GraphQL API (token in URL path, session-based, address server-assigned)
DROPMAIL_BASE = "https://dropmail.me"
# evilmail.pro REST API (session-based token, no API key needed)
EVILMAIL_BASE = "https://evilmail.pro"



# Convenience set: all site names that use the shared Laravel/_tmq_* logic
LARAVEL_SITES = frozenset({
    "tempmailq.com", "maildax.cc", "dakbox.net", "temp-mail-world.com",
    "disposableemailgenerator.com",
    "temporarymailservice.com", "zhimail.xyz", "mailditch.com", "tempmaili.com",
})

# â”€â”€ ANSI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

ANSI = {"reset":"\033[0m","bold":"\033[1m","green":"\033[32m","cyan":"\033[36m",
        "yellow":"\033[33m","red":"\033[31m","dim":"\033[2m","magenta":"\033[35m"}

def c(color, text):
    return f"{ANSI[color]}{text}{ANSI['reset']}" if sys.stdout.isatty() else str(text)

def header(text):
    print(); print(c("cyan","â”€"*60)); print(c("bold",f"  {text}")); print(c("cyan","â”€"*60))
def info(label, value): print(f"  {c('dim',label+':')}  {c('green',str(value))}")
def warn(msg): print(c("yellow",f"  âš   {msg}"))
def err(msg):  print(c("red",   f"  âœ—  {msg}"))
def ok(msg):   print(c("green", f"  âœ”  {msg}"))

# â”€â”€ Cache â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"mailboxes": {}}

def save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

# â”€â”€ Email parsing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def parse_email(raw: str) -> tuple[str, str, str]:
    if "@" not in raw:
        err(f"'{raw}' is not a valid email address (expected user@domain).")
        _print_known_domains()
        sys.exit(1)
    user, domain = raw.split("@", 1)
    user   = user.strip()
    domain = domain.strip().lower()
    if domain not in DOMAIN_MAP:
        err(f"Unknown domain '{domain}'.")
        _print_known_domains()
        sys.exit(1)

    site = DOMAIN_MAP[domain]
    if site == "chatworkon.com" and not user.lower().startswith("tmp"):
        user = "tmp" + user

    return user, domain, site

def _print_known_domains():
    print(f"\n  Known domains:")
    for d, s in DOMAIN_MAP.items():
        print(f"    {d}  â†’  {s}")
