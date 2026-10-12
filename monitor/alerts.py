"""Send PulseWatch email alerts using Gmail."""

import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_alert(subject, message):
    sender = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    receiver = os.getenv("ALERT_EMAIL")
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))

    if not sender or not password or not receiver:
        print("Email settings are missing!")
        return False

    email = EmailMessage()
    email["From"] = sender
    email["To"] = receiver
    email["Subject"] = subject
    email.set_content(message)

    try:
        context = ssl.create_default_context()

        if port == 465:
            with smtplib.SMTP_SSL(
                host, port, timeout=20, context=context
            ) as smtp:
                smtp.login(sender, password)
                smtp.send_message(email)

        elif port == 587:
            with smtplib.SMTP(
                host, port, timeout=20
            ) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(sender, password)
                smtp.send_message(email)

        else:
            raise ValueError("Use SMTP port 465 or 587")

        print("Email alert sent!")
        return True

    except Exception as error:
        print(f"Email failed: {type(error).__name__}: {error}")
        return False
