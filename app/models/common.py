from pydantic import BaseModel


class CitiesDTO(BaseModel):
    id: int
    name: str


class CityExtendedDTO(CitiesDTO):
    is_active: bool
