import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('cli_commands.py', encoding='utf-8') as f:
    txt = f.read()

# Find the tempemail.cc list block - it's missing a print()+return at the end
# The pattern ends with print(f"  {c('dim', ...)} message(s) total")
# then falls through. Need to add print() and return.

OLD = '''        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
    if site == "fakemail.net":
        header(f"Messages in {email_key}")'''

NEW = '''        print(f"  {c('dim', str(len(normalised))+' message(s) total')}")
        print()
        return
    if site == "fakemail.net":
        header(f"Messages in {email_key}")'''

if OLD in txt:
    txt2 = txt.replace(OLD, NEW, 1)
    with open('cli_commands.py', 'w', encoding='utf-8') as f:
        f.write(txt2)
    print("Patched: added return after tempemail.cc list section")
else:
    # Find the area
    idx = txt.find("str(len(normalised))+' message(s) total'")
    while idx != -1:
        snippet = txt[idx:idx+200]
        print(repr(snippet))
        print("---")
        idx = txt.find("str(len(normalised))+' message(s) total'", idx+1)
