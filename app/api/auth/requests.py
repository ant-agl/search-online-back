from fastapi import Form
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr = Form(media_type="application/x-www-form-urlencoded")
    password: str = Form(media_type="application/x-www-form-urlencoded")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Form(media_type="application/x-www-form-urlencoded")
