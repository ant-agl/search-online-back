from pydantic import BaseModel


class RegistryUserResponse(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    type: str = "Bearer"


class BaseResponse(BaseModel):
    status: int
    success: bool
    message: str | None = None

