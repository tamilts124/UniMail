# UniMail

A unified CLI for disposable email — one consistent interface across multiple temp-mail providers (tempmailq.com, maildax.cc, chatworkon.com, tempmailsall.com, dakbox.net, temp-mail-world.com, and disposableemailgenerator.com). Built on `curl_cffi` browser-impersonation sessions so requests aren't fingerprint-blocked.

## Features

- Create, switch, list, and delete disposable mailboxes across multiple providers.
- List and read inbox messages (HTML bodies are parsed/cleaned up into readable formatted CLI text).
- Per-mailbox session persistence: sessions (cookies, CSRF tokens, or JWTs) are cached in `.unimail_cache.json` so your mailboxes survive across runs.
- Verbose `--debug` request/response logging for troubleshooting.
- Automatically handles complex provider details:
  - Laravel-based double CSRF tokens for `tempmailq.com`, `maildax.cc`, `dakbox.net`, `temp-mail-world.com`, and `disposableemailgenerator.com`.
  - JWT Bearer Token authorization and `tmp` username prefix normalization for `chatworkon.com`.
  - WordPress admin-ajax nonces and random mailbox allocation for `tempmailsall.com`.

## Requirements

- Python 3.10+
- [`curl_cffi`](https://github.com/yifeikong/curl_cffi)

```bash
pip install curl_cffi
```

## Project Structure

```
tempmail/
├── unimail.py           # CLI entry point (handles --help and reconfigures UTF-8 encoding)
├── cli_config.py        # shared config, ANSI colors, cache I/O, and email parsing/normalization
├── cli_tmq.py           # Laravel generic client (tempmailq.com & maildax.cc)
├── cli_cwo.py           # chatworkon.com client (JWT authorization and raw email RFC822 parsing)
├── cli_tms.py           # tempmailsall.com client (WordPress admin-ajax nonces & sessions)
├── cli_maildax.py       # maildax.cc helper
├── cli_commands.py      # implementation of each command-line flag
└── .unimail_cache.json  # cached sessions/tokens per mailbox (auto-generated)
```

## Usage

```bash
python unimail.py --help
```

### CLI Commands

| Command | Description |
|---|---|
| `--list-site` | List all supported sites and their domains |
| `--list-domain <site>` | List available domains for a site, e.g., `tempmailq.com` |
| `--mail-id <user@domain>` | Create or reuse a mailbox (e.g. `test@chatcloud.site` or `mytest@wqacmjaqe.xyz`) |
| `--list-message <user@domain>` | List messages in a mailbox |
| `--view-message <user@domain> <n>` | View message #n (1-based index) |
| `--delete-id <user@domain>` | Remove mailbox from local cache (and delete on server if supported) |
| `--real-mail-id <user@domain>` | Get the real mailbox ID for a mock ID (or prints the input itself if not mock) |
| `--debug` | Enable verbose request/response logging (can be appended anywhere) |

### Examples

**Using TempMailQ / Maildax:**
```bash
python unimail.py --mail-id mytest@wqacmjaqe.xyz
python unimail.py --list-message mytest@wqacmjaqe.xyz
python unimail.py --view-message mytest@wqacmjaqe.xyz 1
```

**Using Chatworkon (chatcloud.site):**
```bash
# Note: chatworkon always prepends a 'tmp' prefix to the mailbox address (created as tmptest@chatcloud.site)
python unimail.py --mail-id test@chatcloud.site
python unimail.py --list-message tmptest@chatcloud.site
python unimail.py --view-message tmptest@chatcloud.site 1
```

## Supported Providers & Domains

| Site / Provider | Domains | Protocol / Notes |
|---|---|---|
| **tempmailq.com** | `wqacmjaqe.xyz` | Laravel CSRF (XSRF Header & Meta Token) + Session Cookie |
| **maildax.cc** | `maildax.space`, `maildax.store`, `maildax.online` | Laravel CSRF + Session Cookie |
| **chatworkon.com** | `chatcloud.site` | Stateless JWT Bearer Header + prepended `tmp` username prefix |
| **tempmailsall.com** | `edubd.edu.pl` | WordPress admin-ajax (scraped nonce, session_id allocation) |
| **dakbox.net** | `dakbox.net` | Laravel CSRF + Session Cookie |
| **temp-mail-world.com** | `10-minutes.email` | Laravel CSRF + Session Cookie |
| **disposableemailgenerator.com** | `disposableemailgenerator.com`, `hdhub4u.us` | Laravel CSRF + Session Cookie |
| **temporarymailservice.com** | `tomail.fyi` | Laravel CSRF — FAILED (reCAPTCHA blocks headless) |
| **zhimail.xyz** | `zhimail.xyz`, `zhimail.in`, `zhimails.work`, `zhimails.vip` | Laravel CSRF + Session Cookie (slow, ~45s timeout) |
| **mailditch.com** | `ditch.my.id` | Laravel CSRF — FAILED (reCAPTCHA blocks headless) |
| **tempmaili.com** | `munik.edu.pl` | Laravel CSRF + Session Cookie |
| **mail.tm** | `web-library.net` (+ live from `/domains`) | Public REST API, Bearer JWT |
| **guerrillamail.com** | `guerrillamail.com/net/org/de/biz/info`, `grr.la`, `sharklasers.com`, `spam4.me`, `guerrillamailblock.com` | Public JSON API, `sid_token` session |
| **10minutemail.com** | `vtmpj.com`, `jbsze.net`, `jbsze.com`, `onldm.net`, `gonrr.net` | REST/JSON JSESSIONID cookie session; server-assigned address |
| **10minutemail.net** | `laoia.com` | REST/JSON key-based session — GEO-BLOCKED from IN (403) |
| **openinbox.io** | `inboxly.website`, `inboxfast.space`, `inboxfly.space` | REST API, no auth; server-assigned address |
| **mailinator.com** | `mailinator.com` | Public REST API `/api/v2/domains/public/inboxes/<inbox>`; no auth; stateless |
| **maildrop.cc** | `maildrop.cc` | Public GraphQL API; no auth; stateless |
| **temp-mail.io** | `lnovic.com`, `bwmyga.com`, `yzcalo.com` | Internal REST API `api.internal.temp-mail.io/api/v3`; no auth; server-assigned |
| **freecustom.email** | `ditapi.info`, `addmy.space`, `attachmy.site`, `ditcloud.info`, `ditdrive.info`, `ditgame.info`, `ditlearn.info`, `ditpay.info`, `ditplay.info`, `ditube.info`, `junkstopper.info`, `areueally.info`, `sqlcompiler.info`, `nimbusreach.info`, `lumenbay.info`, `haloforge.online`, `haloforge.info`, `echoharbor.in` | Anonymous JWT REST API; stateless; any `username@domain` works |
| **fakemail.net** | `forliion.com` | PHP session + AJAX endpoints; server-assigned address |
| **tempemail.cc** | `icmans.com` | Internal REST API, Bearer JWT; server-assigned address |
| **tempforward.com** | `tempforward.com` | Token-based REST API; server-assigned address |
| **tempmailo.com** | `denipl.net`, `denipl.com`, `fxzig.com` | ASP.NET Core + Cloudflare; server-assigned; MX does not accept Gmail |
| **1secmail.com** | `1secmail.com`, `1secmail.org`, `1secmail.net`, `wwjmp.com`, `esiix.com`, `xojxe.com`, `yoggm.com` | Public REST API — GEO-BLOCKED from IN (403) |
| **mailmomy.com** | `mailmomy.com`, `2famail.com`, `xikemail.com`, `protect.support`, `easyme.pro`, `282mail.com`, `bsdu32.buzz`, `nuxh62.space`, `doxu243.buzz`, `xue32.buzz`, `evergreenco.shop`, `mingyuekeji.online` | Public REST API; no auth; stateless |
| **catchmail.io** | `catchmail.io` | Public REST API; no auth; stateless |
| **tempmail.plus** | `mailto.plus` | Stateless REST API; user-chosen address |
| **mohmal.com** | `emailinbo.live` | Server-side HTML; curl_cffi cookie session |
| **harakirimail.com** | `harakirimail.com` | Public REST API; no auth; stateless; auto-deleted after 24h |
| **minuteinbox.com** | `minafter.com` | COMPLEX — JS-managed session (MI cookie); cannot reliably work headless |
| **dropmail.me** | `spymail.one`, `pickmail.org`, `emlhub.com`, `emlpro.com`, `emltmp.com`, `freeml.net`, `mail2me.co`, `mailpwr.com`, `mailtowin.com`, `maximail.vip`, `mimimail.me`, `pickmemail.com`, `dropmail.me`, `10mail.info`, `10mail.org`, `10mail.xyz`, `yomail.info` | GraphQL API; session token in URL path |
| **eyepaste.com** | `eyepaste.com` | RSS-based stateless inbox; no auth; emails expire after 1h |
| **48hr.email** | `48hr.email` | Internal REST API; stateless; no auth; emails expire after 48h |
| **evilmail.pro** | `evilbx.com` | REST API; session token returned on create; emails expire after 60 min |
