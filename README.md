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

| Site / Provider | Domain Mapping | Protocol Details |
|---|---|---|
| **tempmailq.com** | `wqacmjaqe.xyz` | Laravel CSRF (XSRF Header & Meta Token) + Session Cookie |
| **maildax.cc** | `maildax.space`, `maildax.store`, `maildax.online` | Laravel CSRF + Session Cookie |
| **chatworkon.com** | `chatcloud.site` | Stateless JWT Bearer Header + prepended `tmp` username prefix |
| **tempmailsall.com** | `edubd.edu.pl` | WordPress admin-ajax (scraped nonce, session_id allocation) |
| **dakbox.net** | `dakbox.net` | Laravel CSRF + Session Cookie |
| **temp-mail-world.com** | `10-minutes.email` | Laravel CSRF + Session Cookie |
| **disposableemailgenerator.com** | `disposableemailgenerator.com`, `hdhub4u.us` | Laravel CSRF + Session Cookie |
