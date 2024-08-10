from abc import ABC, abstractmethod

import sqlalchemy
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import TokenPayload
from app.models.users import UserCreateDTO, UserFillingDTO, ContactDTO, ComponyDataDTO
from app.repository.models import Users, UsersCredentials, UsersContacts, UsersCities
from app.repository.repository import BaseRepository
from app.repository.users.exceptions import UserAlreadyExistsException, UserNotFoundException


class UsersRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def registry(self, user: UserCreateDTO) -> int:
        _user = Users(
            first_name=user.first_name,
            last_name=user.last_name,
        )

        self.session.add(_user)
        await self.session.flush()
        user_id = _user.id
        credentials = UsersCredentials(
            user_id=user_id,
            email=user.email,
            password=user.password
        )
        try:
            self.session.add(credentials)
            await self.session.commit()
            return user_id
        except sqlalchemy.exc.IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsException()

    async def get_credentials(self, email: str) -> str | None:
        statement = select(
            UsersCredentials.password
        ).filter_by(
            email=email
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, login: str) -> TokenPayload:
        statement = select(
            Users
        ).join(UsersCredentials).filter_by(
            email=login
        )
        result = await self.session.execute(statement)
        result = result.scalar()
        if result is None:
            raise UserNotFoundException()
        return TokenPayload(
            id=result.id,
            type=result.type.value
            if result.type is not None else None,
            full_filled=result.full_filled,
        )

    async def get_user_token_data_by_id(self, user_id: int) -> TokenPayload:
        statement = select(
            Users
        ).filter_by(
            id=user_id
        )
        result = await self.session.execute(statement)
        result = result.scalar()
        if result is None:
            raise UserNotFoundException()
        return TokenPayload(
            id=result.id,
            full_filled=result.full_filled,
            type=result.type.value
            if result.type is not None else None
        )

    async def drop_error_user(self, user_id: int):
        statement = delete(
            Users
        ).filter_by(
            id=user_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def fill_profile(self, user_id: int, data: UserFillingDTO) -> None:
        statement = update(
            Users
        ).filter_by(
            id=user_id
        ).values(
            type=data.type.value,
            full_filled=True
        )
        city = UsersCities(
            user_id=user_id,
            city_id=data.city_id
        )
        self.session.add(city)
        result = await self.session.execute(statement)
        await self.session.commit()

    async def add_contacts(self, user_id: int, contacts: list[ContactDTO]):
        contacts = [
            UsersContacts(
                user_id=user_id,
                type=contact.type.value,
                value=contact.value,
                is_hidden=contact.hidden
            )
            for contact in contacts
        ]

        self.session.add_all(contacts)
        await self.session.commit()

    async def add_compony_data(self, user_id: int, company_data: ComponyDataDTO):
        pass

