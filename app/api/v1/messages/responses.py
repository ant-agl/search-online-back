from pydantic import BaseModel

from app.models.messages import Message, MessageMeta


class MessagesResponse(BaseModel):
    messages: list[Message]
    meta: MessageMeta