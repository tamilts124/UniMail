#!/usr/bin/env python3
"""
cli_config.py - shared config, ANSI helpers, cache I/O, and email parsing
for the unimail.py CLI.

Split out of the original monolithic unimail.py so each concern
(config/ansi/cache, tempmailq client, maildax client, commands, entry point)
can be edited independently.
"""

import sys, os, json, time

# ── Config ────────────────────────────────────────────────────────────────────

CACHE_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".unimail_cache.json")
IMPERSONATE  = "chrome124"
HTTP_TIMEOUT = 20

DEBUG = os.environ.get("UNIMAIL_DEBUG", "0") == "1"

def set_debug(value: bool):
    """Toggle debug output at runtime (used by --debug CLI flag)."""
    global DEBUG
    DEBUG = value

def dbg(msg):
    if DEBUG:
        print(f"[{time.strftime('%H:%M:%S')}] DEBUG: {msg}", file=sys.stderr, flush=True)

SITE_DOMAINS = {
    "tempmailq.com": ["wqacmjaqe.xyz"],
    "maildax.cc":    ["maildax.space", "maildax.store", "maildax.online"],
}

def _build_domain_map() -> dict[str, str]:
    m = {}
    for site, domains in SITE_DOMAINS.items():
        for d in domains:
            m[d] = site
    return m

DOMAIN_MAP = _build_domain_map()

TEMPMAILQ_BASE = "https://tempmailq.com"
MAILDAX_BASE   = "https://maildax.cc"

# ── ANSI ──────────────────────────────────────────────────────────────────────

ANSI = {"reset":"\033[0m","bold":"\033[1m","green":"\033[32m","cyan":"\033[36m",
        "yellow":"\033[33m","red":"\033[31m","dim":"\033[2m","magenta":"\033[35m"}

def c(color, text):
    return f"{ANSI[color]}{text}{ANSI['reset']}" if sys.stdout.isatty() else str(text)

def header(text):
    print(); print(c("cyan","─"*60)); print(c("bold",f"  {text}")); print(c("cyan","─"*60))
def info(label, value): print(f"  {c('dim',label+':')}  {c('green',str(value))}")
def warn(msg): print(c("yellow",f"  ⚠  {msg}"))
def err(msg):  print(c("red",   f"  ✗  {msg}"))
def ok(msg):   print(c("green", f"  ✔  {msg}"))

# ── Cache ─────────────────────────────────────────────────────────────────────

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

# ── Email parsing ─────────────────────────────────────────────────────────────

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
    return user, domain, DOMAIN_MAP[domain]

def _print_known_domains():
    print(f"\n  Known domains:")
    for d, s in DOMAIN_MAP.items():
        print(f"    {d}  →  {s}")
