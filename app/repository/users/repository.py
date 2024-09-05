from abc import ABC, abstractmethod
from typing import Union

import sqlalchemy
from babel.dates import format_date
from sqlalchemy import select, delete, update, func, literal, Float, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.v1.users.requests import CreateSellerReviewRequest
from app.models.auth import TokenPayload
from app.models.common import ReviewsByStarsDTO
from app.models.users import UserCreateDTO, UserFillingDTO, ContactDTO, CompanyDataDTO, UserDTO, ContactsDTO, ReviewDTO, \
    UserShortDTO
from app.repository.models import Users, UsersCredentials, UsersContacts, UsersCities, Cities, UserAvatar, UsersType, \
    SellersReviews, UserReports, LegalInfo, SellersCategories
from app.repository.repository import BaseRepository
from app.repository.users.exceptions import UserAlreadyExistsException, UserNotFoundException
from app.utils.types import TypesOfUser


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
            types=[
                tp.type.value
                for tp in result.type
            ]
            if result.type else [],
            full_filled=result.full_filled,
            is_blocked=result.is_blocked,
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
            types=[
                tp.type.value
                for tp in result.type
            ]
            if result.type else [],
            is_blocked=result.is_blocked,
        )

    async def delete(self, user_id: int):
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
            full_filled=True
        )
        details = []
        city = UsersCities(
            user_id=user_id,
            city_id=data.city_id
        )
        details.append(city)
        if data.main_category:
            user_categories = []
            for d in data.main_category:
                user_categories.append(SellersCategories(
                    user_id=user_id,
                    category_id=d
                ))
            details.extend(user_categories)
        self.session.add_all(details)
        await self.session.execute(statement)

    async def add_type(self, user_id: int, _type: TypesOfUser) -> None:
        __type = UsersType(
            user_id=user_id,
            type=_type.value
        )
        self.session.add(__type)

    async def add_contacts(self, user_id: int, contacts: list[ContactDTO]):
        contacts = [
            UsersContacts(
                user_id=user_id,
                type=contact.type.value,
                value=contact.value,
                is_hidden=contact.is_hidden
            )
            for contact in contacts
        ]

        self.session.add_all(contacts)

    async def add_compony_data(self, user_id: int, company_data: CompanyDataDTO):
        company_data = LegalInfo(
            user_id=user_id,
            type=company_data.type.value,
            **company_data.model_dump(exclude_none=True, exclude={"type"})
        )
        self.session.add(company_data)

    async def is_exist(self, user_id: int):
        statement = select(
            Users
        ).filter_by(
            id=user_id
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def update(self, user_id: int, user_data: dict):
        statement = update(
            Users
        ).filter_by(
            id=user_id
        ).values(
            **user_data
        )
        await self.session.execute(statement)

    async def update_city(self, user_id: int, city_id: int):
        statement = update(
            UsersCities
        ).filter_by(
            user_id=user_id
        ).values(
            city_id=city_id
        )
        await self.session.execute(statement)

    async def get_user_contacts(self, user_id: int):
        statement = select(
            UsersContacts
        ).filter_by(
            user_id=user_id
        )
        result = await self.session.execute(statement)
        result = result.scalars().all()
        return result

    async def update_contact(self, contact_id: int, data: dict):
        statement = update(
            UsersContacts
        ).filter_by(
            id=contact_id
        ).values(
            **data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def delete_contact(self, contact_id: int):
        statement = delete(
            UsersContacts
        ).filter_by(
            id=contact_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def save_avatar_link(self, user_id: int, key: str):
        avatar = UserAvatar(
            user_id=user_id,
            link=key
        )
        self.session.add(avatar)
        await self.session.commit()

    async def get(self, user_id: int, extended: bool = False):
        statement = select(
            Users
        ).filter_by(
            id=user_id
        ).options(joinedload(
            Users.user_city,
        )).options(joinedload(
            Users.avatar
        )).options(joinedload(
            Users.contacts
        )).options(joinedload(
            Users.legal_info
        ))
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        result = result[0]
        return UserDTO(
            id=result.id,
            first_name=result.first_name,
            last_name=result.last_name,
            middle_name=result.middle_name,
            types=result.types,
            city=result.city,
            city_id=result.user_city.city_id,
            avatar=result.avatar.link if result.avatar else None,
            contacts=[
                ContactsDTO.model_validate(contact, from_attributes=True)
                for contact in result.contacts
            ],
            full_filled=result.full_filled,
            is_blocked=result.is_blocked,
            legal_info=CompanyDataDTO.model_validate(
                result.legal_info, from_attributes=True
            ) if extended else None,
            rating=result.rating if extended else None,
            updated_at=result.updated_at,
        )

    async def users_types(self, users: list[int]):
        statement = select(
            Users
        ).filter(
            Users.id.in_(users)
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if len(result) < 2 and len(users) > 1:
            return None
        users_types = {}
        for user in result:
            users_types[user.id] = user.types
        return users_types

    async def create_review(
            self, from_user_id: int, to_user_id: int,
            body: CreateSellerReviewRequest
    ):
        review = SellersReviews(
            seller_id=to_user_id,
            from_user_id=from_user_id,
            stars=body.stars,
            text=body.text,
        )
        self.session.add(review)
        await self.session.commit()

    async def delete_review(self, review_id: int):
        statement = delete(
            SellersReviews
        ).filter_by(
            id=review_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get_review_owner(self, review_id: int):
        statement = select(
            SellersReviews.from_user_id
        ).filter_by(
            id=review_id
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_reviews(self, criteria: dict, offset: int, limit: int):
        statement = select(
            SellersReviews
        ).filter_by(
            **criteria
        ).options(
            joinedload(SellersReviews.from_user)
        ).offset(offset).limit(limit)
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return []
        return [
            ReviewDTO(
                user=UserShortDTO(
                    id=review.from_user.id,
                    full_name=review.from_user.full_name,
                    city=review.from_user.city,
                    avatar=review.from_user.avatar.link if review.from_user.avatar else None,
                ),
                stars=review.stars,
                text=review.text,
                created_at=format_date(
                    review.created_at, format="d MMMM y", locale="ru"
                )
            )
            for review in result
        ]

    async def get_reviews_quantity(self, criteria: dict):
        statement = select(
            func.count(SellersReviews.id)
        ).filter_by(
            **criteria
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_grouped_reviews(self, user_id: int, stars: list[float], is_seller: bool = False):
        stars_cte = union_all(
                *[
                    select(literal(val).label(f"stars"))
                    for val in stars
                ]
        ).cte("stars_range")

        statement = select(
            stars_cte,
            func.count(SellersReviews.id)
        ).outerjoin(
            SellersReviews, stars_cte.c.stars == SellersReviews.stars
        ).group_by(
            stars_cte.c.stars
        ).order_by(
            stars_cte.c.stars.desc()
        ).filter(
            (SellersReviews.seller_id == user_id)
            if is_seller else (SellersReviews.from_user_id == user_id)
        )
        result = await self.session.execute(statement)
        result = result.fetchall()
        if not result:
            return []
        return [
            ReviewsByStarsDTO(
                star=res[0],
                quantity=res[1]
            )
            for res in result
        ]

    async def add_report(self, from_user_id: int, to_user_id: int, reason: str):
        report = UserReports(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            reason=reason,
        )
        self.session.add(report)
        await self.session.commit()

    async def get_reports_quantity(self, to_user_id: int):
        statement = select(
            func.count(UserReports.id)
        ).filter_by(
            to_user_id=to_user_id
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def block_user(self, user_id: int):
        statement = update(
            Users
        ).filter_by(
            id=user_id
        ).values(
            is_blocked=True
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get_user_categories(self, user_id: int):
        statement = select(
            SellersCategories.category_id
        ).filter_by(
            user_id=user_id
        )
        result = await self.session.execute(statement)
        result = result.scalars().all()
        if not result:
            return None
        return result


