import asyncio
import math

from app.api.v1.requests.requests import NewRequest
from app.api.v1.requests.responses import Meta, RequestsResponse, RequestResponse
from app.models.auth import TokenPayload
from app.repository.requests.repository import RequestsRepository
from app.services.common.service import CommonService
from app.services.offers.service import OffersService
from app.services.requests.exceptions import CreateRequestException, RequestException, RequestNotFound
from app.services.service import BaseService
from app.services.users.service import UserService


class RequestsService(BaseService):

    _repository: RequestsRepository

    def __init__(self, repository: RequestsRepository):
        super().__init__(repository)

    async def add_request(self, user: TokenPayload, body: NewRequest, common_service: CommonService):
        if not user.full_filled:
            raise CreateRequestException(
                "Для создания запроса, профиль должен быть заполнен"
            )

        category = await common_service.check_category(body.category_id)
        if category.disabled:
            raise CreateRequestException(
                f"Категория({category.value}) в данный момент не активна"
            )
        if category.on_moderating:
            raise CreateRequestException(
                f"Категория({category.value}) находиться на модерации"
            )

        request_id = await self._repository.add(user.id, body)
        return request_id

    async def get_requests_for_seller(
            self, user: TokenPayload, common_service: CommonService,
            users_service: UserService, by_category: bool,
            page: int, page_limit: int
    ):
        if "seller" not in user.types:
            raise RequestException("Вы не являетесь продавцом")

        categories = None
        warning = None
        if by_category:
            sellers_categories = await users_service.get_my_categories(user.id)
            if sellers_categories:
                categories = await common_service.get_categories_what_depend_on(
                    sellers_categories
                )
            else:
                warning = "У вас не выбрана основная категория"

        offset = (page - 1) * page_limit

        total = self._repository.total_requests(categories=categories)
        request = self._repository.get_for_seller(
            offset, page_limit,
            categories=categories
        )

        total, request = await asyncio.gather(
            total, request
        )

        meta = Meta(
            page=page,
            total_items=total,
            total_pages=math.ceil(total / page_limit),
            items_per_page=page_limit
        )
        return RequestsResponse(
            requests=request,
            meta=meta,
            warning=warning
        )

    async def requests_for_creator(self, user_id, page, page_limit):
        offset = (page - 1) * page_limit

        total = self._repository.total_requests(creator_id=user_id)
        requests = self._repository.get_my_requests(
            user_id, offset=offset, limit=page_limit
        )

        total, requests = await asyncio.gather(
            total, requests
        )

        meta = Meta(
            page=page,
            total_items=total,
            total_pages=math.ceil(total / page_limit),
            items_per_page=page_limit
        )

        return RequestsResponse(
            requests=requests,
            meta=meta,
        )

    async def get_request_by_id(
            self, request_id: int, user_id: int, offers_service: OffersService,
            page: int, limit: int
    ):
        creator_id = await self._repository.get_request_creator(request_id)

        if creator_id is None:
            raise RequestNotFound(request_id)

        is_creator = False
        if creator_id == user_id:
            is_creator = True

        request = await self._repository.get(request_id,)
        offers = None
        meta = None
        if is_creator:
            offers = await offers_service.get_offers_by_criteria(
                {
                    "request_id": request_id,
                    "status": "PENDING"
                }, page, limit, exclude=["request"]
            )
            offers, meta = offers

        return RequestResponse(
            request=request,
            offers=offers,
            meta=meta.model_dump()
        ).model_dump(exclude_none=True)

    async def delete(self, request_id: int, user_id: int):
        creator_id = await self._repository.get_request_creator(request_id)
        if creator_id is None:
            raise RequestNotFound(request_id)
        if creator_id != user_id:
            raise RequestException(
                "Вы не можете удалить запрос, который отправили не вы"
            )
        await self._repository.delete(request_id)
        return True


