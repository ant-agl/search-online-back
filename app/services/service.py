import logging

from app.repository.repository import BaseRepository


class BaseService:
    _repository: BaseRepository

    def __init__(self, repository: BaseRepository):
        self._repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def rollback(self):
        await self._repository.session.rollback()

    async def commit(self):
        await self._repository.session.commit()


