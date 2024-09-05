from sqlalchemy import select, delete, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import user

from app.models.users import UserShortDTO
from app.repository.models import OffersThreads, ThreadsParticipants
from app.repository.repository import BaseRepository


class MessagesRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_thread(self, from_user: int, to_user: int, offer_id: int):
        thread = OffersThreads(
            offer_id=offer_id,
        )
        self.session.add(thread)
        await self.session.flush()
        thread_id = thread.id
        participants = [
            ThreadsParticipants(
                thread_id=thread_id,
                user_id=from_user,
            ),
            ThreadsParticipants(
                thread_id=thread_id,
                user_id=to_user,
            )
        ]
        self.session.add_all(participants)
        await self.session.commit()
        return thread_id

    async def get_user_threads(self, user_id: int):
        statement = select(
            ThreadsParticipants.thread_id
        ).filter_by(
            user_id=user_id
        )
        threads = await self.session.execute(statement)
        threads = threads.scalars().all()
        return threads

    async def delete_thread(self, thread_id: int):
        statement = delete(OffersThreads).filter_by(id=thread_id)
        await self.session.execute(statement)
        await self.session.commit()

    async def check_dialog_exists(self, offer_id: int, user_id: int, to_user: int):
        statement = select(OffersThreads.id).join(
            ThreadsParticipants, OffersThreads.id == ThreadsParticipants.thread_id
        ).where(
            and_(
                OffersThreads.offer_id == offer_id,
                ThreadsParticipants.user_id.in_([user_id, to_user])
            )
        )
        result = await self.session.execute(statement)
        result = result.scalars().all()
        return result

    async def thread_participant(self, thread_id: int):
        statement = select(
            ThreadsParticipants.thread_id, ThreadsParticipants.user_id
        ).filter_by(
            thread_id=thread_id
        )
        result = await self.session.execute(statement)
        result = result.all()
        if not result:
            return None
        return [
            res[1]
            for res in result
        ]
    
    async def get_participants_info(self, thread_id):
        statement = select(
            ThreadsParticipants
        ).options(
            joinedload(ThreadsParticipants.user)
        ).filter_by(
            thread_id=thread_id
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        return [
            thread.user.to_short_dto()
            for thread in result
        ]

