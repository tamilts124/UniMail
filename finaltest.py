import smtplib, ssl, os, time, subprocess, json
from email.mime.text import MIMEText

addr = 'algcaerba@yomail.info'
msg = MIMEText('Dropmail.me CLI integration test - final verification')
msg['Subject'] = 'Dropmail CLI test final'
msg['From'] = os.environ['EMAIL_USERNAME']
msg['To'] = addr

ctx = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx) as s:
    s.login(os.environ['EMAIL_USERNAME'], os.environ['EMAIL_APP_PASSWORD'])
    s.send_message(msg)
print(f'Sent to {addr}')

time.sleep(45)

r = subprocess.run(['python', 'unimail.py', '--list-message', 'testclaude@spymail.one'],
                   capture_output=True, text=True, cwd=r'D:\ClaudeDir\tempmail')
print('Result:', r.stdout.strip()[:400])
with open(r'D:\ClaudeDir\tempmail\finalcheck.txt', 'w') as f:
    f.write(r.stdout)
