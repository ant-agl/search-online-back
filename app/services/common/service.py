from app.models.common import CitiesDTO
from app.repository.common.repository import CommonRepository
from app.services.common.exceptions import CityNotFoundException, CityNotActiveException
from app.services.service import BaseService


class CommonService(BaseService):
    _repository: CommonRepository

    def __init__(self, repository: CommonRepository):
        super().__init__(repository)

    async def get_all(
            self, query: str | None = None,
            offset: int | None = None, limit: int | None = None
    ) -> list[CitiesDTO]:
        return await self._repository.get_all(query, offset, limit)

    async def check_city(self, city_id: int) -> bool:
        result = await self._repository.check_city_active(city_id)
        if result is None:
            raise CityNotFoundException(city_id)
        if not result.is_active:
            raise CityNotActiveException(result.name)
        return True
