from app.api.v1.requests.requests import NewRequest
from app.models.auth import TokenPayload
from app.repository.requests.repository import RequestsRepository
from app.services.common.service import CommonService
from app.services.requests.exceptions import CreateRequestException, RequestException
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
            users_service: UserService, page: int, page_limit: int
    ):
        if "seller" not in user.types:
            raise RequestException("Вы не являетесь продавцом")

        sellers_categories = await users_service.get_my_categories(user.id)
        categories = None
        if sellers_categories:
            categories = await common_service.get_categories_what_depend_on(
                sellers_categories
            )

        offset = (page - 1) * page_limit

        total = self._repository.total_requests_for_seller(categories)
        request = self._repository.get_for_seller(
            offset, page_limit,
            categories=categories
        )




