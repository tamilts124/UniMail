import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Credentials extracted from browser localStorage
EMAIL = "naia2022@icmans.com"
ACCOUNT_ID = "204742330215829504"
PASSWORD = "PpJ*h8wGl9"
TOKEN = "eyJhbGciOiJFZERTQSJ9.eyJpYXQiOjE3ODQ0NzUxNzUsImlkIjoiMjA0NzQyMzMwMjE1ODI5NTA0Iiwib3duZXJJZCI6IjIwNDc0MjMzMDIxNTgyOTUwNCIsIm1haWxib3hUeXBlIjowLCJtZXJjdXJlIjp7InN1YnNjcmliZSI6WyIvdS8yMDQ3NDIzMzAyMTU4Mjk1MDQiXX19.-XzOuYfZXOaUF7uuj9b6lSL8R1TUUiqZjY-66z412YzG8O5rIMPdBm-5zJYNTltkwAkUd81WUF-VXMGtCk-CBA"

with open('.unimail_cache.json', encoding='utf-8') as f:
    cache = json.load(f)

cache.setdefault('mailboxes', {})[EMAIL] = {
    'tempemail_token': TOKEN,
    'tempemail_account_id': ACCOUNT_ID,
    'tempemail_password': PASSWORD,
}

with open('.unimail_cache.json', 'w', encoding='utf-8') as f:
    json.dump(cache, f, indent=2)

print(f"Injected tempemail session for {EMAIL}")
print(f"Account ID: {ACCOUNT_ID}")
print(f"Token: {TOKEN[:40]}...")
