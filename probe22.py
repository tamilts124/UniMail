import urllib.request, sys

services = [
    ('temppostal.com', 'https://api.temppostal.com/v1/emails'),
    ('inboxes.com', 'https://inboxes.com/api/v1/inbox/testclaude'),
    ('mailpoof.com', 'https://mailpoof.com/api/inbox/testclaude'),
    ('trashmail.com', 'https://trashmail.com/api/1/list.json?account=testclaude'),
    ('tmpmail.net', 'https://tmpmail.net/api/inbox/testclaude'),
    ('jetable.fr', 'https://www.jetable.fr/api/v1/inbox/testclaude'),
    ('maildrop.cc', 'https://api.maildrop.cc/v2/mailbox/testclaude'),
    ('spamgourmet.com', 'https://www.spamgourmet.com/api/inbox/testclaude'),
    ('tempr.email', 'https://tempr.email/api/inbox/testclaude'),
]
for name, url in services:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=8)
        body = r.read()[:100]
        sys.stderr.write(f'OK {name}: {r.status} {body}\n')
    except Exception as e:
        sys.stderr.write(f'FAIL {name}: {str(e)[:70]}\n')
sys.stderr.write('done\n')
