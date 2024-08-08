import logging
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)
