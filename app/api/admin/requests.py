from pydantic import BaseModel


class AddFAQ(BaseModel):
    question: str
    answer: str
