from app.models.common import CitiesDTO
from app.repository.common.repository import CommonRepository
from app.services.service import BaseService


class CommonService(BaseService):
    repository: CommonRepository

    def __init__(self, repository: CommonRepository):
        super().__init__(repository)

    async def get_all(
            self, query: str | None = None,
            offset: int | None = None, limit: int | None = None
    ) -> list[CitiesDTO]:
        return await self.repository.get_all(query, offset, limit)
