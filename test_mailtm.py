import smtplib, os, sys
from email.mime.text import MIMEText

username = os.environ.get('EMAIL_USERNAME', '')
password = os.environ.get('EMAIL_APP_PASSWORD', '')
to_addr = 'mailtmtest2026@web-library.net'
subject = 'UniMail Test - mail.tm 2026-07-19'

print(f'Sending to {to_addr} from {username}, password_len={len(password)}', flush=True)
msg = MIMEText('UniMail integration test for mail.tm. Timestamp: 2026-07-19')
msg['Subject'] = subject
msg['From'] = username
msg['To'] = to_addr

try:
    s = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
    s.login(username, password)
    s.sendmail(username, [to_addr], msg.as_string())
    s.quit()
    print('SENT OK', flush=True)
except Exception as e:
    print(f'ERROR: {e}', flush=True)
    sys.exit(1)
