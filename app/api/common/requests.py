from pydantic import BaseModel


class CreateCategory(BaseModel):
    name: str
    depend_on: int | None = None
