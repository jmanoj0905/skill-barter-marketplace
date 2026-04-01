from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
