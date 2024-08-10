import asyncio
import pprint

from app.api.v1.users.requests import RegistryUserRequest, FullRegistryUserRequest
from app.models.auth import TokenPayload
from app.models.users import UserCreateDTO, UserFillingDTO, ContactDTO, ComponyDataDTO
from app.repository.users.exceptions import UserAlreadyExistsException
from app.repository.users.repository import UsersRepository
from app.services.service import BaseService
from app.services.users.exceptions import UserNotFoundException


class UserService(BaseService):
    _repository: UsersRepository

    def __init__(self, repository: UsersRepository):
        super().__init__(repository)

    async def registry(self, user: RegistryUserRequest) -> int:
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
        company_data = None
        if body.type.value == "seller":
            # TODO: Логика проверки данных компании
            company_data = ComponyDataDTO(
                legal_format=body.company_data.legal_format,
                company_name=body.company_data.company_name,
                address=body.company_data.address,
                description=body.company_data.description,
            )
        profile_data = UserFillingDTO(
            city_id=body.city_id,
            type=body.type,
            main_category=body.main_category
        )
        contacts = [
            ContactDTO(
                type=contact.type.value,
                value=contact.value,
                hidden=contact.hidden
            )
            for contact in body.contacts
        ]
        coroutines = [
            self._repository.fill_profile(user_id, profile_data),
            self._repository.add_contacts(user_id, contacts)
        ]
        if company_data is not None:
            coroutines.append(
                self._repository.add_compony_data(user_id, company_data)
            )

        await asyncio.gather(*coroutines)
        return True

    async def rollback(self):
        await self._repository.session.rollback()

    async def commit(self):
        await self._repository.session.commit()

    async def drop_error(self, user_id: int):
        await self._repository.drop_error_user(user_id)


