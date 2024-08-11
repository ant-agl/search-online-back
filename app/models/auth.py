from pydantic import BaseModel


class TokenPayload(BaseModel):
    id: int
    type: str | None = None
    full_filled: bool
    is_blocked: bool
