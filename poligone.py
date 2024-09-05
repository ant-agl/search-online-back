from pydantic import BaseModel


class Poligone(BaseModel):
    id: int
    name: str


class Poligones(BaseModel):
    items: list[Poligone]


obg = Poligones(
    items=[
        Poligone(id=9, name="str"),
        Poligone(id=10, name="int"),
    ]
)

obj = {
    "items": [
        {"id": 9, "name": "str"},
        {"id": 10, "name": "int"},
    ]
}

print(Poligones.model_validate(obj))