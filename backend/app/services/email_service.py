import smtplib
import time
from email.mime.text import MIMEText
from app.core.config import settings


def send_email(to_email: str, subject: str, body: str):

    retries = 3
    delay = 2

    for attempt in range(retries):

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_EMAIL
            msg["To"] = to_email

            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()

            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)

            server.sendmail(
                settings.SMTP_EMAIL,
                to_email,
                msg.as_string()
            )

            server.quit()

            print(f"Email sent to {to_email}")

            return True

        except Exception as e:

            print(f"Email send failed (attempt {attempt+1}): {e}")

            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2

    return False

def send_otp_email(email: str, otp: str):

    subject = "Your Skill Barter Email Verification OTP"

    body = f"""
Hello,

Your email verification OTP is:

{otp}

This OTP will expire in 10 minutes.

If you did not request this, please ignore this email.

Skill Barter Marketplace
"""

    return send_email(email, subject, body)

def send_reset_email(email: str, reset_token: str):

    subject = "Password Reset Request"

    body = f"""
Hello,

You requested a password reset.

Use this reset token:

{reset_token}

This token will expire in 6 hours.

If you did not request this, ignore this email.

Skill Barter Marketplace
"""

    return send_email(email, subject, body)

def send_reset_email(email: str, reset_token: str):

    subject = "Password Reset Request"

    body = f"""
Hello,

You requested a password reset.

Use this reset token:

{reset_token}

This token will expire in 6 hours.

If you did not request this, ignore this email.

Skill Barter Marketplace
"""

    return send_email(email, subject, body)