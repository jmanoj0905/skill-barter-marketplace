from twilio.rest import Client
from app.core.config import settings
import time

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_sms(phone: str, message: str):

    retries = 3
    delay = 2

    for attempt in range(retries):

        try:
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE,
                to=phone
            )

            print(f"SMS sent to {phone}")
            return True

        except Exception as e:

            print(f"SMS send failed (attempt {attempt+1}): {e}")

            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2

    return False


def send_otp_sms(phone: str, otp: str):

    message = f"""
Skill Barter OTP Verification

Your OTP is: {otp}

Valid for 10 minutes.
"""

    return send_sms(phone, message)