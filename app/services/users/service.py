from app.api.v1.users.requests import RegistryUserRequest, FullRegistryUserRequest
from app.models.auth import TokenPayload
from app.models.users import UserCreateDTO
from app.repository.users.exceptions import UserAlreadyExistsException
from app.repository.users.repository import UsersRepository
from app.services.service import BaseService
from app.services.users.exceptions import UserNotFoundException


class UserService(BaseService):
    _repository: UsersRepository

    def __init__(self, repository: UsersRepository):
        super().__init__(repository)

    async def registry(self, user: RegistryUserRequest):
        try:
            user = UserCreateDTO.model_validate(user, from_attributes=True)
            user_id = await self._repository.registry(user)
            return user_id
        except UserAlreadyExistsException as e:
            raise e

    async def get_user_password(self, user_login: str) -> str:
        password = await self._repository.get_credentials(user_login)
        if password is None:
            raise UserNotFoundException()
        return password

    async def get_user_by_email(self, login: str) -> TokenPayload:
        return await self._repository.get_user_by_email(login)

    async def get_user_token_data_by_id(self, user_id: int) -> TokenPayload:
        return await self._repository.get_user_token_data_by_id(user_id)

    async def fill_profile(self, user_id: int, body: FullRegistryUserRequest):
        pass

