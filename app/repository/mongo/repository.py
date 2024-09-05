import datetime
import logging

import pymongo
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.messages import NewMessage, Message


class MongoRepository:
    def __init__(self, db:  AsyncIOMotorDatabase):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def add_message(self, message: NewMessage):
        message_data = message.model_dump()
        message_data["read"] = False
        result = await self.db.messages.insert_one(message_data)
        return str(result.inserted_id)

    async def get_messages_by_thread(self, thread_id: int, limit: int, offset: int):
        messages = await self.db.messages.find({
            "thread_id": thread_id,
        }).sort(
            "created_at", -1
        ).skip(offset).limit(limit).to_list(length=limit)
        if not messages:
            return []
        messages = list(
            map(lambda x: {**x, "id": str(x["_id"])}, messages)
        )
        return [
            Message.model_validate(message)
            for message in messages
        ]

    async def get_total_messages(self, thread_id: int):
        count = await self.db.messages.count_documents({
            "thread_id": thread_id
        })
        return count

    async def set_read(self, messages_ids: list[str], receiver_id: int):
        result = await self.db.messages.update_many({
            "$and": [
                {"_id": {"$in": list(map(lambda x: ObjectId(x), messages_ids))}},
                {"to_user.id": receiver_id}
            ]
        }, {
            "$set": {"read": True}
        })
        if result.modified_count == len(messages_ids):
            return True
        elif result.modified_count > 1:
            return True
        else:
            return False

    async def update_message(self, message_id: str, content: str):
        result = await self.db.messages.update_one({
            "_id": ObjectId(str(message_id)),
        }, {
            "$set": {
                "content": content,
                "updated_at": datetime.datetime.now(
                    datetime.UTC
                ).strftime("%d-%m-%Y %H:%M:%S")
            }
        })
        if result.modified_count == 1:
            return True

    async def delete_message(self, message_id: str):
        result = await self.db.messages.delete_one({
            "_id": ObjectId(message_id),
        })
        if result.deleted_count == 1:
            return True

    async def get_message_by_id(self, message_id: str, user_id: int):
        result = await self.db.messages.find_one({
            "$and": [
                {"_id": ObjectId(message_id)}, {"from_user.id": user_id}
            ]
        })
        if not result:
            return None
        return True

    async def get_unread_messages(self, user_id: int):
        pipeline = [
            {"$match": {"to_user.id": user_id, "read": False}},
            {
                "$group": {
                    "_id": "$thread_id",
                    "unread": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "unread": 1,
                    "thread_id": "$_id",
                }
            }
        ]
        unread_messages = self.db.messages.aggregate(pipeline)
        unread_messages = await unread_messages.to_list(length=1)
        return unread_messages

    async def get_latest_message(self, user_id: int, threads_ids: list[int] = None):
        pipeline = [
            {"$match": {"thread_id": {"$in": [10]}}},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$thread_id",
                    "latest_message": {"$first": "$$ROOT"},
                }
            },
            {"$replaceRoot": {"newRoot": "$latest_message"}},
            {
                "$project": {
                    "_id": 1,
                    "from_user": 1,
                    "to_user": 1,
                    "thread_id": 1,
                    "content": 1,
                    "created_at": 1,
                    "read": 1,
                }
            }
        ]
        latest_message = self.db.messages.aggregate(pipeline)
        latest_message = await latest_message.to_list(length=None)
        return latest_message

    async def get_latest_messages_with_unread_count(
            self, user_id: int, threads_ids: list[int]
    ):
        pipeline = [
            {"$match": {"thread_id": {"$in": threads_ids}}},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$thread_id",
                    "latest_message": {"$first": "$$ROOT"},
                    "unread_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$eq": ["$read", False]},
                                        {"$eq": ["$to_user.id", user_id]},
                                    ]
                                },
                                1, 0
                            ]
                        }
                    }
                }
            },
            {"$replaceRoot": {"newRoot": {
                "_id": "$latest_message._id",
                "from_user": "$latest_message.from_user",
                "to_user": "$latest_message.to_user",
                "thread_id": "$latest_message.thread_id",
                "content": "$latest_message.content",
                "created_at": "$latest_message.created_at",
                "read": "$latest_message.read",
                "unread_count": "$unread_count"
            }}},
            {"$sort": {"created_at": -1}},
            {
                "$project": {
                    "_id": 1,
                    "from_user": 1,
                    "to_user": 1,
                    "thread_id": 1,
                    "content": 1,
                    "created_at": 1,
                    "read": 1,
                    "unread_count": 1,
                }
            }
        ]

        latest_message = self.db.messages.aggregate(pipeline)
        latest_message = await latest_message.to_list(length=None)
        return latest_message

    async def delete_thread(self, thread_id: int):
        result = await self.db.messages.delete_many({"thread_id": thread_id})
        if result.deleted_count > 0:
            return True
        

