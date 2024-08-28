from pydantic import BaseModel


class CitiesDTO(BaseModel):
    id: int
    name: str


class CityExtendedDTO(CitiesDTO):
    is_active: bool


class CategoryDTO(BaseModel):
    id: int
    type: str
    value: str
    depend_on: int | None = None
    on_moderating: bool
    disabled: bool


class CategoryShortDTO(BaseModel):
    id: int
    type: str
    value: str


class ReviewsByStarsDTO(BaseModel):
    star: float
    quantity: int


class FAQsDTO(BaseModel):
    id: int
    question: str
    answer: str
