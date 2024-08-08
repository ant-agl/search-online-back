from pydantic import BaseModel

from app.api.v1.users.requests import RegistryUserRequest


class UserCreateDTO(RegistryUserRequest):
    pass
