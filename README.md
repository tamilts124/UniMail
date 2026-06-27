# UniMail

A unified CLI and TUI for disposable email — one consistent interface across
multiple temp-mail providers (tempmailq.com, maildax.cc, and more). Built on
`curl_cffi` browser-impersonation sessions so requests aren't fingerprint-blocked.

## Features

- Create, switch, and delete disposable mailboxes across providers
- List and read inbox messages (HTML bodies are cleaned up into readable text)
- Per-mailbox session persistence (cookies + CSRF tokens cached to disk, so
  you don't have to re-create a mailbox every run)
- Verbose `--debug` request/response logging
- Handles tempmailq.com's dual CSRF scheme (XSRF-TOKEN cookie *and* a Laravel
  meta `_token`) automatically, including token rotation and 419 retries

## Requirements

- Python 3.10+
- [`curl_cffi`](https://github.com/yifeikong/curl_cffi)
- [`rich`](https://github.com/Textualize/rich) (TUI only)
- [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/) (TUI only)

```bash
pip install curl_cffi rich beautifulsoup4
```

## Project Structure

```
tempmail/
├── unimail.py           # CLI entry point
├── cli_config.py        # shared config, ANSI colors, cache I/O, email parsing
├── cli_tmq.py           # tempmailq.com client (sessions, CSRF, requests)
├── cli_maildax.py       # maildax.cc client (CLI side, partial)
├── cli_commands.py      # implementation of each --flag command
├── main.py              # interactive TUI entry point (rich-based)
├── modules/
│   ├── tempmailq.py     # tempmailq.com client class, used by main.py
│   └── maildax.py       # standalone maildax.cc client class
└── .unimail_cache.json  # cached sessions/tokens per mailbox (auto-generated)
```

## Usage

### CLI (`unimail.py`)

```bash
python unimail.py --help
```

| Command | Description |
|---|---|
| `--list-site` | List all supported sites and their domains |
| `--list-domain <site>` | List available domains for a site, e.g. `tempmailq.com` |
| `--mail-id <user@domain>` | Create or reuse a mailbox |
| `--list-message <user@domain>` | List messages in a mailbox |
| `--view-message <user@domain> <n>` | View message #n (1-based) |
| `--delete-id <user@domain>` | Delete a mailbox on the server and from local cache |
| `--debug` | Verbose request/response logging (combine with any command) |

Example:

```bash
python unimail.py --mail-id mytest@wqacmjaqe.xyz
python unimail.py --list-message mytest@wqacmjaqe.xyz
python unimail.py --view-message mytest@wqacmjaqe.xyz 1
```

### Interactive TUI (`main.py`)

```bash
python main.py
```

A menu-driven `rich` interface for tempmailq.com: refresh inbox, create a new
address, browse address history, or delete & regenerate the current mailbox.

## Known Domains

| Domain | Provider |
|---|---|
| wqacmjaqe.xyz | tempmailq.com |
| maildax.space / maildax.store / maildax.online | maildax.cc |

(Domain lists are refreshed live from each site's homepage where possible.)

## Notes

- `maildax.cc` support is implemented as a standalone client
  (`modules/maildax.py`) but isn't yet wired into the CLI or TUI command flow.
- Session/token state is cached locally (`.unimail_cache.json` for the CLI,
  `session.json` for the TUI) so mailboxes survive across runs.
