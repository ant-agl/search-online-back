import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.users import UserShortDTO


class NewMessage(BaseModel):
    thread_id: int
    from_user: UserShortDTO | dict
    to_user: UserShortDTO | dict
    content: str
    created_at: str
    updated_at: str


class Message(NewMessage):
    id: str
    read: bool


class ThreadMessage(NewMessage):
    id: int
    messages: list[Message]
    total: int


class MessageMeta(BaseModel):
    total_messages: int
    current_offset: int
    current_limit: int