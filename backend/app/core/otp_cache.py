import random
from datetime import datetime, timedelta

# temporary memory storage
otp_store = {}
otp_request_count = {}


def generate_otp():
    return str(random.randint(100000, 999999))


def store_otp(email: str, otp: str):

    expiry_time = datetime.utcnow() + timedelta(minutes=10)

    otp_store[email] = {
        "otp": otp,
        "expires": expiry_time
    }


def is_otp_valid(email: str, otp: str):

    data = otp_store.get(email)

    if not data:
        return False

    if datetime.utcnow() > data["expires"]:
        return False

    return data["otp"] == otp


def check_rate_limit(email: str):

    now = datetime.utcnow()

    if email not in otp_request_count:
        otp_request_count[email] = []

    # remove old requests
    otp_request_count[email] = [
        t for t in otp_request_count[email]
        if now - t < timedelta(hours=1)
    ]

    if len(otp_request_count[email]) >= 3:
        return False

    otp_request_count[email].append(now)

    return True

def remove_otp(email: str):
    if email in otp_store:
        del otp_store[email]