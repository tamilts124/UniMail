import smtplib, ssl, os
from email.mime.text import MIMEText
msg = MIMEText('Test email for dropmail.me CLI integration verification')
msg['Subject'] = 'Test dropmail integration'
msg['From'] = os.environ['EMAIL_USERNAME']
msg['To'] = 'bawypig1huzem4@mimimail.me'
ctx = ssl.create_default_context()
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx) as s:
    s.login(os.environ['EMAIL_USERNAME'], os.environ['EMAIL_APP_PASSWORD'])
    s.send_message(msg)
print('Sent OK')
