import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('domains_list.txt', encoding='utf-8') as f:
    txt = f.read()

# freecustom.email: PENDING -> IMPLEMENTED TESTED
txt = txt.replace(
    'https://freecustom.email/ [PENDING]',
    'https://freecustom.email/ [IMPLEMENTED] [TESTED] -> cli_freecustom.py | anonymous JWT REST API | stateless | any username@domain works | domains: ditapi.info addmy.space attachmy.site + 15 more | VERIFIED email received at testclaude3@addmy.space'
)

# fakemail.net: PENDING -> IMPLEMENTED TESTED
txt = txt.replace(
    'https://fakemail.net/ [PENDING]',
    'https://fakemail.net/ [IMPLEMENTED] [TESTED] -> cli_fakemail.py | PHP session + AJAX endpoints | address server-assigned | domain: forliion.com | BOM fix applied | VERIFIED email received at testclaude99@forliion.com'
)

with open('domains_list.txt', 'w', encoding='utf-8') as f:
    f.write(txt)
print("domains_list.txt updated: freecustom.email and fakemail.net -> [IMPLEMENTED] [TESTED]")
