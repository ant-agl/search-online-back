import asyncio
import datetime
import logging
from typing import Literal

from cryptography.fernet import Fernet

from app.models.messages import NewMessage, MessageMeta
from app.repository.messages.repository import MessagesRepository
from app.repository.mongo.repository import MongoRepository
from app.services.messages.exceptions import ThreadAlreadyExists, ThreadException, MessageNotFoundException, \
    ThreadNotFoundException
from app.services.offers.service import OffersService
from app.settings import settings


class MessagesService:
    __mongo_repository: MongoRepository
    __postgres_repository: MessagesRepository

    def __init__(
            self, mongo_repository: MongoRepository,
            postgres_repository: MessagesRepository
    ):
        self.__mongo_repository = mongo_repository
        self.__postgres_repository = postgres_repository
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cifer = Fernet(settings.ENCODE_KEY.encode())

    async def create_thread(
            self, user_id: int, offer_id: int, offer_service: OffersService
    ):
        offer_participants: list[int] = await offer_service.offer_participants(offer_id, user_id)
        offer_participants.remove(user_id)
        to_user_id = offer_participants[0]
        
        if user_id == to_user_id:
            raise ThreadException("Нельзя создать диалог с самим собой")

        check = await self.__postgres_repository.check_dialog_exists(
            offer_id, user_id, to_user_id
        )
        if check:
            if len(check) == 2 and len(set(check)) == 1:    
                raise ThreadAlreadyExists()

        thread_id = await self.__postgres_repository.create_thread(
            user_id, to_user_id, offer_id
        )
        return thread_id

    async def delete_thread(self, thread_id: int, user_id: int):
        await self.__participants(
            thread_id, user_id,
            "Вы не можете удалить диалог, участником, которого вы не являетесь"
        )
        await asyncio.gather(
            self.__postgres_repository.delete_thread(thread_id),
            self.__mongo_repository.delete_thread(thread_id)
        )

    async def send_message(self, thread_id: int, user_id: int, content: str):
        await self.__participants(
            thread_id, user_id,
            "Вы не можете отправить сообщение в диалог, "
            "участником, которого вы не являетесь"
        )
        users = await self.__postgres_repository.get_participants_info(
            thread_id
        )
        if len(users) < 2:
            raise ThreadException("Невозможно отправить сообщение в данный диалог")
        
        from_user = None
        to_user = None
        
        for user in users:
            if user.id == user_id:
                from_user = user
            to_user = user
            
        message_body = NewMessage(
            thread_id=thread_id,
            from_user=from_user,
            to_user=to_user,
            content=self.cifer.encrypt(content.encode()).decode("utf-8"),
            created_at=datetime.datetime.now(datetime.UTC).strftime("%d-%m-%Y %H:%M:%S"),
            updated_at=datetime.datetime.now(datetime.UTC).strftime("%d-%m-%Y %H:%M:%S")            
        )
        message_id = await self.__mongo_repository.add_message(message_body)
        return message_id
    
    async def __participants(self, thread_id: int, user_id: int, err_message: str):
        participants = await self.__postgres_repository.thread_participant(
            thread_id
        )
        if participants is None:
            raise ThreadNotFoundException(
                "Диалог не найден"
            )
        if user_id not in participants:
            raise ThreadException(
                err_message
            )
        
    async def get_messages(self, thread_id: int, user_id: int, offset: int, limit: int):
        await self.__participants(
            thread_id, user_id,
            "Вы не являетесь участником диалога"
        )
        messages = self.__mongo_repository.get_messages_by_thread(
            thread_id, limit, offset
        )
        total = self.__mongo_repository.get_total_messages(
            thread_id
        )
        
        messages, total = await asyncio.gather(
            messages, total
        )
        messages_list = []
        for message in messages:
            if message.from_user.id == user_id:
                message.from_user = message.from_user.model_dump()
                message.from_user["is_me"] = True
            elif message.to_user.id == user_id:
                message.to_user = message.to_user.model_dump()
                message.to_user["is_me"] = True

            message.content = self.cifer.decrypt(message.content.encode("utf-8")).decode("utf-8")
            
        meta = MessageMeta(
            total_messages=total,
            current_offset=offset,
            current_limit=limit
        )
        
        return messages, meta

    async def update_or_delete_message(
            self, thread_id: int, message_id: str,
            user_id: int, content: str = None, _type: Literal[
                "del", "upd"
            ] = "upd"
    ):
        await self.__participants(
            thread_id, user_id,
            "Вы не являетесь участником данного диалога"
        )
        message = await self.__mongo_repository.get_message_by_id(
            message_id, user_id
        )
        if message is None:
            raise MessageNotFoundException(
                "Сообщение не найдено"
            )

        result = False

        if _type == "upd":
            result = await self.__mongo_repository.update_message(
                message_id, content=content
            )
        elif _type == "del":
            result = await self.__mongo_repository.delete_message(
                message_id
            )

        return result

    async def mark_as_read(self, thread_id: int, ids: list[str], user_id: int):
        await self.__participants(
            thread_id, user_id, "Вы не являетесь участником данного диалога"
        )
        result = await self.__mongo_repository.set_read(ids, user_id)
        return result

    async def unread_message_quantity(self, user_id: int):
        result = await self.__mongo_repository.get_unread_messages(user_id)
        result = sum([rs["unread"] for rs in result])
        return result

    async def get_user_threads(
            self, user_id: int, offset: int = None, limit: int = None
    ):
        users_threads = await self.__postgres_repository.get_user_threads(user_id)
        threads = await self.__mongo_repository.get_latest_messages_with_unread_count(
            user_id, users_threads
        )
        threads = list(map(lambda x: {**x, "id": str(x["_id"])}, threads))

        result = []
        for thread in threads:
            item = {
                "thread_id": thread["thread_id"],
                "unread_count": thread["unread_count"],
            }
            thread.pop("thread_id")
            thread.pop("unread_count")
            thread.pop("_id")
            content = thread["content"]
            thread["content"] = self.cifer.decrypt(
                content.encode("utf-8")
            ).decode("utf-8")
            item["last_message"] = thread
            result.append(item)

        return result

    async def update_user_avatar(self, user_id: int, avatar_url: str ):
        await self.__mongo_repository.update_user_avatat(user_id, avatar_url)


