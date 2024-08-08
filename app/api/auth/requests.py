from fastapi import Form
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr = Form()
    password: str = Form()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Form()
