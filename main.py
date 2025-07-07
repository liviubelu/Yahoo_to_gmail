from flask import Flask
import threading
import smtplib
import email
import os
from imapclient import IMAPClient

# ------------------- Flask pentru UptimeRobot -------------------
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Serverul funcționează continuu."

def start_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=start_flask).start()

# ----------------- Script Yahoo → Gmail -------------------------
yahoo_user = os.getenv('YAHOO_USER')
yahoo_pass = os.getenv('YAHOO_PASS')
gmail_user = os.getenv('GMAIL_USER')
gmail_pass = os.getenv('GMAIL_PASS')

if not all([yahoo_user, yahoo_pass, gmail_user, gmail_pass]):
    print("❌ Variabilele de mediu lipsesc!")
    exit(1)

try:
    server = IMAPClient('imap.mail.yahoo.com', ssl=True)
    server.login(yahoo_user, yahoo_pass)
    server.select_folder('INBOX', readonly=True)

    messages = server.search(['UNSEEN'])

    for uid, message_data in server.fetch(messages[-3:], ['RFC822']).items():
        raw_email = message_data[b'RFC822']
        msg = email.message_from_bytes(raw_email)

        subject = msg["Subject"] or "(Fără subiect)"
        sender = msg["From"] or "(Necunoscut)"
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and part.get_payload(decode=True):
                    charset = part.get_content_charset() or 'utf-8'
                    body = part.get_payload(decode=True).decode(charset, errors="ignore")
                    break
        else:
            charset = msg.get_content_charset() or 'utf-8'
            body = msg.get_payload(decode=True).decode(charset, errors="ignore")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(gmail_user, gmail_pass)
            smtp.sendmail(
                from_addr=gmail_user,
                to_addrs=gmail_user,
                msg=f"Subject: FWD from Yahoo: {subject}\n\nFrom: {sender}\n\n{body}"
            )

    print("✅ Emailuri Yahoo transferate cu succes.")

except Exception as e:
    print(f"❌ Eroare: {e}")
