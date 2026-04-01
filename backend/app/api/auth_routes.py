from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.services.auth_service import register_user, authenticate_user
from app.core.security import create_access_token
from app.api.deps import get_db
from app.core.security import create_access_token, create_refresh_token
from fastapi import Header
from app.core.token_blacklist import blacklist_token
from fastapi import HTTPException
from pydantic import BaseModel
from app.services.auth_service import forgot_password, reset_password
from app.services.auth_service import verify_email_otp
from app.services.auth_service import generate_email_otp
from app.services.auth_service import resend_email_otp
from app.services.auth_service import generate_phone_otp
from app.services.auth_service import verify_phone_otp

router = APIRouter(prefix="/auth", tags=["Auth"])
from pydantic import BaseModel

class PhoneOTPRequest(BaseModel):
    phone: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class EmailOTPRequest(BaseModel):
    email: str

class VerifyEmailOTPRequest(BaseModel):
    email: str
    otp: str

class ResendOTPRequest(BaseModel):
    email: str

class VerifyPhoneOTPRequest(BaseModel):
    phone: str
    otp: str

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):

    try:
        user = register_user(
            db,
            request.email,
            request.password,
            request.name,
            request.phone
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "User registered successfully"}


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):

    user = authenticate_user(db, request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(authorization: str = Header(...)):

    token = authorization.replace("Bearer ", "")

    blacklist_token(token)

    return {"message": "User logged out successfully"}


@router.post("/forgot-password")
def forgot_password_endpoint(request: ForgotPasswordRequest, db: Session = Depends(get_db)):

    try:
        reset_token = forgot_password(db, request.email)

        return {
            "message": "Password reset token generated",
            "reset_token": reset_token
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
def reset_password_endpoint(request: ResetPasswordRequest, db: Session = Depends(get_db)):

    try:
        reset_password(db, request.token, request.new_password)

        return {
            "message": "Password reset successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/generate-email-otp")
def generate_email_otp_endpoint(request: EmailOTPRequest, db: Session = Depends(get_db)):

    try:
        otp = generate_email_otp(db, request.email)

        return {
            "message": "OTP generated successfully",
            "otp": otp
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/verify-email-otp")
def verify_email_otp_endpoint(request: VerifyEmailOTPRequest, db: Session = Depends(get_db)):

    try:
        verify_email_otp(db, request.email, request.otp)

        return {
            "message": "Email verified successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/resend-email-otp")
def resend_email_otp_endpoint(request: ResendOTPRequest, db: Session = Depends(get_db)):

    try:
        otp = resend_email_otp(db, request.email)

        return {
            "message": "OTP resent successfully",
            "otp": otp
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/generate-phone-otp")
def generate_phone_otp_endpoint(request: PhoneOTPRequest, db: Session = Depends(get_db)):

    try:
        otp = generate_phone_otp(db, request.phone)

        return {
            "message": "Phone OTP generated successfully",
            "otp": otp
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/verify-phone-otp")
def verify_phone_otp_endpoint(request: VerifyPhoneOTPRequest, db: Session = Depends(get_db)):

    try:
        verify_phone_otp(db, request.phone, request.otp)

        return {
            "message": "Phone verified successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))