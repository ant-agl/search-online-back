from pydantic import BaseModel


class TokenPayload(BaseModel):
    user_id: int
    type: str | None = None
    full_filled: bool
