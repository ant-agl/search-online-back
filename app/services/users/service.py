import asyncio
import pprint
import uuid

from app.api.v1.users.requests import RegistryUserRequest, FullRegistryUserRequest, UpdateUserRequest, Contacts, \
    UpdateContactRequest
from app.api.v1.users.responses import UserResponse, UserInfo, CityInfo, UserAvatar
from app.models.auth import TokenPayload
from app.models.users import UserCreateDTO, UserFillingDTO, ContactDTO, ComponyDataDTO, UpdateUserDTO, ContactsDTO, \
    UserDTO
from app.repository.users.exceptions import UserAlreadyExistsException
from app.repository.users.repository import UsersRepository
from app.services.cloud_service import CloudService
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
                is_hidden=contact.is_hidden
            )
            for contact in body.contacts
        ]
        coroutines = [
            self._repository.fill_profile(user_id, profile_data),
            self._repository.add_contacts(user_id, contacts),
            self._repository.add_type(user_id, body.type)
        ]
        if company_data is not None:
            coroutines.append(
                self._repository.add_compony_data(user_id, company_data)
            )

        await asyncio.gather(*coroutines)
        await self.commit()
        return True

    async def update_profile(self, user_id: int, body: UpdateUserRequest):
        user_exist = await self._repository.is_exist(user_id=user_id)
        if user_exist is None:
            raise UserNotFoundException()
        user_data = UpdateUserDTO(
            first_name=body.first_name,
            last_name=body.last_name,
            middle_name=body.middle_name,
        ).model_dump(exclude_none=True)
        coroutines = [
            self._repository.update(user_id, user_data),
        ]
        if body.city_id is not None:
            coroutines.append(
                self._repository.update_city(user_id, body.city_id),
            )

        await asyncio.gather(*coroutines)
        await self.commit()
        return True

    async def get_contacts(self, user_id: int) -> list[ContactsDTO]:
        contacts = await self._repository.get_user_contacts(user_id)
        if not contacts:
            raise UserNotFoundException()
        return [
            ContactsDTO.model_validate(contact, from_attributes=True)
            for contact in contacts
        ]

    async def add_contact(self, user_id: int, body: Contacts):
        user_exist = await self._repository.is_exist(user_id=user_id)
        if user_exist is None:
            raise UserNotFoundException()
        contact = ContactDTO.model_validate(body, from_attributes=True)
        await self._repository.add_contacts(user_id, [contact])
        return True

    async def update_contact(
            self, user_id: int,
            contact_id: int, data: UpdateContactRequest
    ):
        user_exist = await self._repository.is_exist(user_id=user_id)
        if user_exist is None:
            raise UserNotFoundException()
        await self._repository.update_contact(contact_id, data.model_dump(
            exclude_none=True
        ))

    async def delete_contacts(
            self, user_id: int, contact_id: int
    ):
        user_exist = await self._repository.is_exist(user_id=user_id)
        if user_exist is None:
            raise UserNotFoundException()
        await self._repository.delete_contact(contact_id)

    async def update_avatar(
            self, user_id: int, photo: bytes, cloud: CloudService
    ):
        user_exist = await self._repository.is_exist(user_id=user_id)
        if user_exist is None:
            raise UserNotFoundException()
        key = f"avatar-{user_id}.png"
        link = cloud.get_link(f"avatar-{user_id}.png")
        await cloud.session()
        await asyncio.gather(*[
            self._repository.save_avatar_link(user_id, link),
            cloud.save_file(photo, key)
        ])

    async def get_user_profile(self, user_id: int):
        user: UserDTO | None = await self._repository.get(
            user_id=user_id
        )
        if user is None:
            raise UserNotFoundException()
        user_info = UserInfo(
            first_name=user.first_name,
            last_name=user.last_name,
            middle_name=user.middle_name,
            type=user.type.value,
        )
        city = CityInfo(
            id=user.city_id,
            name=user.city,
        )
        avatar = UserAvatar(
            value=user.avatar
        )
        return UserResponse(
            id=user.id,
            info=user_info,
            city=city,
            avatar=avatar,
            contacts=user.contacts,
            full_filled=user.full_filled,
            is_blocked=user.is_blocked,
            updated_at=str(user.updated_at),
        )

    async def drop_user(self, user_id: int):
        await self._repository.delete(user_id)

    async def get_users_types(self, from_user_id: int, to_user_id: int = None):
        result = await self._repository.users_types([from_user_id, to_user_id])
        if result is None:
            raise UserNotFoundException()
        return result

