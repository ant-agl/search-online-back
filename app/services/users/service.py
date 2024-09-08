import asyncio
import math
import pprint
import uuid

from sqlalchemy.exc import IntegrityError

from app.api.v1.users.requests import RegistryUserRequest, FullRegistryUserRequest, UpdateUserRequest, Contacts, \
    UpdateContactRequest, CreateSellerReviewRequest, CompanyData
from app.api.v1.users.responses import UserResponse, UserInfo, CityInfo, UserAvatar, ReviewsResponse, Meta
from app.models.auth import TokenPayload
from app.models.users import UserCreateDTO, UserFillingDTO, ContactDTO, CompanyDataDTO, UpdateUserDTO, ContactsDTO, \
    UserDTO
from app.repository.users.exceptions import UserAlreadyExistsException
from app.repository.users.repository import UsersRepository
from app.services.cloud_service import CloudService
from app.services.items.service import ItemsService
from app.services.service import BaseService
from app.services.users.exceptions import UserNotFoundException, AssertionUserReviewException, ReviewException, \
    ReviewNotFoundException, AlreadySellerException, SelfReportException
from app.utils.types import TypesOfUser


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
            company_data = CompanyDataDTO(
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

    async def get_user_profile(self, user_id: int, types: list[str]):
        extend = False
        if "seller" in types:
            extend = True

        user: UserDTO | None = await self._repository.get(
            user_id=user_id, extended=extend
        )
        if user is None:
            raise UserNotFoundException()
        user_info = UserInfo(
            first_name=user.first_name,
            last_name=user.last_name,
            middle_name=user.middle_name,
            types=user.types,
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
            legal_info=user.legal_info if extend else None,
            rating=user.rating,
            full_filled=user.full_filled,
            is_blocked=user.is_blocked,
            updated_at=str(user.updated_at),
        ).model_dump(exclude_none=True)

    async def drop_user(self, user_id: int):
        await self._repository.delete(user_id)

    async def get_users_types(self, from_user_id: int, to_user_id: int = None):
        result = await self._repository.users_types([from_user_id, to_user_id])
        if result is None:
            raise UserNotFoundException()
        return result

    async def create_review(
            self, from_user_id: int, to_user_id: int,
            body: CreateSellerReviewRequest
    ):
        if from_user_id == to_user_id:
            raise AssertionUserReviewException("Вы не можете оставить отзыв самому себе")
        to_user_types = await self._repository.users_types([to_user_id])
        if to_user_types is None:
            raise UserNotFoundException()
        if "seller" not in to_user_types[to_user_id]:
            raise ReviewException("Вы не можете оставить только о продавце")
        try:
            await self._repository.create_review(from_user_id, to_user_id, body)
            return True
        except IntegrityError:
            raise ReviewException("Вы уже оставляли отзыв об этом продавце")

    async def delete_review(self, review_id: int, user_id: int):
        owner_id = await self._repository.get_review_owner(review_id)
        if owner_id is None:
            raise ReviewNotFoundException(review_id)
        if owner_id != user_id:
            raise AssertionUserReviewException("Вы не можете удалить отзыв, который писали не вы")
        await self._repository.delete_review(review_id)

    async def get_reviews_about_me(
            self, user: TokenPayload,
            page: int, page_limit: int,
            by_stars: int | None = None
    ):
        if "seller" not in user.types:
            raise ReviewException("Услуга доступна только продавцам")

        offset = (page - 1) * page_limit

        criteria = {
            "seller_id": user.id,
        }

        if by_stars is not None:
            criteria["stars"] = by_stars
        stars_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        total_review_by_stars = self._repository.get_grouped_reviews(
            user.id, stars_values, is_seller=True
        )
        total_items = self._repository.get_reviews_quantity(criteria)
        reviews = self._repository.get_reviews(criteria, offset, page_limit)
        reviews, total_items, total_reviews = await asyncio.gather(
            reviews, total_items, total_review_by_stars
        )

        meta = Meta(
            page=page,
            total_items=total_items,
            total_pages=(total_items + page_limit - 1) // page_limit,
            items_per_page=page_limit,
        )

        return ReviewsResponse(
            by_stars=total_reviews,
            result=reviews,
            meta=meta,
        )

    async def get_reviews_from_me(
            self, user_id: int, value: str,
            page: int, page_limit: int,
            item_service: ItemsService,
            by_stars: int | None = None,
    ):
        offset = (page - 1) * page_limit

        criteria = {
            "from_user_id": user_id,
        }

        if by_stars is not None:
            criteria["stars"] = by_stars
        stars_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        total_items = 0
        reviews = []
        total_reviews = 0
        if value == "seller":
            total_review_by_stars = self._repository.get_grouped_reviews(
                user_id, stars_values
            )
            total_items = self._repository.get_reviews_quantity(criteria)
            reviews = self._repository.get_reviews(criteria, offset, page_limit)
            reviews, total_items, total_reviews = await asyncio.gather(
                reviews, total_items, total_review_by_stars
            )
        elif value in ["item", "service"]:
            reviews, total_items, total_reviews = (
                await item_service.get_reviews_from_user(
                    user_id, value, offset, page_limit,
                )
            )

        meta = Meta(
            page=page,
            total_items=total_items,
            total_pages=(total_items + page_limit - 1) // page_limit,
            items_per_page=page_limit,
        )

        return ReviewsResponse(
            by_stars=total_reviews,
            result=reviews,
            meta=meta,
        )

    async def become_seller(self, user_id: int, body: CompanyData):
        user_types = await self._repository.users_types([user_id])
        if user_types is None:
            raise UserNotFoundException()
        if "seller" in user_types[user_id]:
            raise AlreadySellerException()
        await asyncio.gather(
            self._repository.add_type(user_id, TypesOfUser.seller),
            self._repository.add_compony_data(user_id, CompanyDataDTO.model_validate(
                body, from_attributes=True
            ))
        )
        await self.commit()
        return True

    async def add_report(self, from_user_id: int, to_user_id: int, reason: str):
        if from_user_id == to_user_id:
            raise SelfReportException()

        try:
            await self._repository.add_report(from_user_id, to_user_id, reason)
            reports_quantity = await self._repository.get_reports_quantity(to_user_id)
            if reports_quantity == 3:
                await self._repository.block_user(to_user_id)
            return True
        except IntegrityError:
            return True

    async def get_my_categories(self, user_id: int):
        return await self._repository.get_user_categories(user_id)

    async def get_user_city_id(self, user_id: int):
        return await self._repository.get_city_id(user_id)




