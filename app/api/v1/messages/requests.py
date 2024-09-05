from pydantic import BaseModel


class NewMessageRequest(BaseModel):
    content: str


class MarkAsReadRequest(BaseModel):
    ids: list[str]
