import smtplib
import email
import os
import time
from flask import Flask
from threading import Thread
from imapclient import IMAPClient
from email.message import EmailMessage

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Serverul funcționează continuu.'

def process_emails():
    yahoo_user = os.environ.get('YAHOO_USER')
    yahoo_pass = os.environ.get('YAHOO_PASS')
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_pass = os.environ.get('GMAIL_PASS')

    if not all([yahoo_user, yahoo_pass, gmail_user, gmail_pass]):
        print("❌ Variabilele de mediu lipsă.")
        return

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
            original_to = msg["To"] or "(Necunoscut)"
            date = msg["Date"] or "(Necunoscut)"
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors="ignore")
                        break
            else:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors="ignore")

            forwarded = EmailMessage()
            forwarded['Subject'] = subject
            forwarded['From'] = sender
            forwarded['To'] = gmail_user

            forwarded.set_content(f"""
--- Forwarded message ---
From: {sender}
To: {original_to}
Date: {date}
Subject: {subject}

{body}
            """)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(gmail_user, gmail_pass)
                smtp.send_message(forwarded)

        print("✅ Emailuri Yahoo forwardate cu succes.")
    except Exception as e:
        print(f"❌ Eroare: {e}")

def run_loop():
    while True:
        process_emails()
        time.sleep(60)

if __name__ == '__main__':
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    run_loop()
