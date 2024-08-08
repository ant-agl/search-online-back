from pydantic import BaseModel


class CitiesDTO(BaseModel):
    id: int
    name: str
