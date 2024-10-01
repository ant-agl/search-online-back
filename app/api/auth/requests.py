from fastapi import Form
from pydantic import BaseModel, EmailStr


class LoginRequest:
    def __init__(self, email: EmailStr = Form(...), password: str = Form(...)):
        self.email = email
        self.password = password


class RefreshTokenRequest:
    def __init__(self, refresh_token: str = Form(...)):
        self.refresh_token = refresh_token


class PasswordResetRequest(BaseModel):
    email: EmailStr


class NewPasswordSet(BaseModel):
    verification_code: str
    new_password: str
