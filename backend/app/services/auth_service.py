from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.services.sms_service import send_otp_sms
from app.models.identity_score import IdentityConfidenceScore
from app.models.identity_score import IdentityConfidenceScore
from app.core.security import (
    hash_password,
    verify_password,
    validate_password,
    create_reset_token,
    decode_token
)

from app.core.otp_cache import (
    generate_otp,
    store_otp,
    check_rate_limit,
    is_otp_valid,
    remove_otp
)

from app.services.email_service import (
    send_otp_email,
    send_reset_email
)


# -------------------------
# User Registration
# -------------------------
def register_user(db: Session, email: str, password: str, name: str, phone: str | None):

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise Exception("Email already registered")

    # Validate password strength
    validate_password(password)

    new_user = User(
        email=email,
        name=name,
        phone=phone,
        password_hash=hash_password(password),
        trust_score=0.3,
        email_verified=False,
        phone_verified=False,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# -------------------------
# Login Authentication
# -------------------------
def authenticate_user(db: Session, email: str, password: str):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    user.last_login_at = datetime.utcnow()
    db.commit()

    return user


# -------------------------
# Forgot Password
# -------------------------
def forgot_password(db: Session, email: str):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise Exception("Email not found")

    reset_token = create_reset_token({"sub": str(user.id)})

    # send reset email
    send_reset_email(user.email, reset_token)

    print(f"Password reset requested for user {user.email}")

    return reset_token


# -------------------------
# Reset Password
# -------------------------
def reset_password(db: Session, token: str, new_password: str):

    payload = decode_token(token)

    user_id = payload.get("sub")

    if not user_id:
        raise Exception("Invalid reset token")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise Exception("User not found")

    # Validate password
    validate_password(new_password)

    # Update password
    user.password_hash = hash_password(new_password)

    db.commit()

    print(f"Password successfully reset for user {user.email}")

    return True


# -------------------------
# Generate Email OTP
# -------------------------
def generate_email_otp(db: Session, email: str):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise Exception("Email not found")

    if not check_rate_limit(email):
        raise Exception("OTP request limit exceeded (3 per hour)")

    otp = generate_otp()

    store_otp(email, otp)

    # send OTP email
    send_otp_email(email, otp)

    print(f"OTP generated and sent to {email}")

    return otp


# -------------------------
# Verify Email OTP
# -------------------------
def verify_email_otp(db: Session, email: str, otp: str):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise Exception("User not found")

    if not is_otp_valid(email, otp):
        raise Exception("Invalid OTP")

    user.email_verified = True

    score = calculate_identity_confidence(user)
    user.trust_score = score

    history = IdentityConfidenceScore(
        user_id=user.id,
        confidence_score=score,
        breakdown="email_verified"
    )

    db.add(history)

    db.commit()

    remove_otp(email)

    return True


# -------------------------
# Resend Email OTP
# -------------------------
def resend_email_otp(db: Session, email: str):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise Exception("Email not found")

    if not check_rate_limit(email):
        raise Exception("OTP resend limit exceeded (3 per hour)")

    otp = generate_otp()

    store_otp(email, otp)

    # send OTP again
    send_otp_email(email, otp)

    print(f"OTP resent to {email}")

    return otp


# -------------------------
# Generate Phone OTP
# -------------------------
def generate_phone_otp(db: Session, phone: str):

    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        raise Exception("Phone number not found")

    # Rate limit check
    if not check_rate_limit(phone):
        raise Exception("OTP request limit exceeded (3 per hour)")

    # Generate OTP
    otp = generate_otp()

    # Store OTP in cache
    store_otp(phone, otp)

    # Log OTP generation
    send_otp_sms(phone, otp)

    return otp


    # -------------------------
# Verify Phone OTP
# -------------------------
def verify_phone_otp(db: Session, phone: str, otp: str):

    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        raise Exception("User not found")

    if not is_otp_valid(phone, otp):
        raise Exception("Invalid or expired OTP")

    user.phone_verified = True

    score = calculate_identity_confidence(user)
    user.trust_score = score

    history = IdentityConfidenceScore(
        user_id=user.id,
        confidence_score=score,
        breakdown={
            "base": 0.25,
            "email": 0.20 if user.email_verified else 0,
            "phone": 0.25
        }
    )

    db.add(history)

    db.commit()

    remove_otp(phone)

    return True
# ADD HERE
def calculate_identity_confidence(user):

    score = 0.25

    if user.email_verified:
        score += 0.20

    if user.phone_verified:
        score += 0.25

    if score > 1.0:
        score = 1.0

    return score