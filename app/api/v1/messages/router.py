import logging
from typing import Union

from fastapi import APIRouter, Depends, Query
from starlette.responses import JSONResponse

from app.api.dependencies import get_offers_service, get_messages_service
from app.api.exceptions import InternalServerError, NotFoundApiException, BadRequestApiException, ErrorResponse
from app.api.v1.messages.requests import NewMessageRequest, MarkAsReadRequest
from app.api.v1.messages.responses import MessagesResponse
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.messages.exceptions import ThreadAlreadyExists, ThreadException, MessageNotFoundException, \
    ThreadNotFoundException
from app.services.messages.service import MessagesService
from app.services.offers.exceptions import OfferNotFoundException, OfferNotBelongYouException
from app.services.offers.service import OffersService

router = APIRouter(
    prefix="/messages",
)
logger = logging.getLogger("MessagesRouter")


@router.post("/thread", summary="Создать обсуждение")
async def create_thread(
        offer_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
        offer_service: OffersService = Depends(get_offers_service)
):
    try:
        thread_id = await service.create_thread(
            user_id=user.id,
            offer_id=offer_id,
            offer_service=offer_service
        )
        return JSONResponse(content={"thread_id": thread_id}, status_code=201)
    except OfferNotFoundException as e:
        raise NotFoundApiException(str(e))
    except (OfferNotBelongYouException, ThreadAlreadyExists) as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
    

@router.delete(
    "/thread/{thread_id}", summary="Удалить диалог",
    status_code=204
)
async def delete_thread(
        thread_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
):
    try:
        await service.delete_thread(thread_id, user.id)
    except ThreadException as e:
        raise BadRequestApiException(str(e))
    except ThreadNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
    

@router.post(
    "/thread/{thread_id}/message", summary="Отправить сообщение",
    status_code=201
)
async def send_message(
        thread_id: int,
        body: NewMessageRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service), 
):
    try:
        message_id = await service.send_message(thread_id, user.id, body.content)
        return JSONResponse(
            content={
                "message_id": message_id
            }, status_code=201
        )
    except ThreadException as e:
        raise BadRequestApiException(str(e))
    except ThreadNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/thread/{thread_id}/messages", summary="Получить сообщения в чате",
    status_code=200, response_model_exclude_none=True, response_model=Union[MessagesResponse, ErrorResponse]
)
async def get_messages(
        thread_id: int,
        offset: int = Query(default=0),
        limit: int = Query(default=10),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service), 
):
    try:
        result, meta = await service.get_messages(
            thread_id, user.id, offset, limit
        )
        return MessagesResponse(
            messages=result,
            meta=meta
        )
    except ThreadException as e:
        raise BadRequestApiException(str(e))
    except ThreadNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.put(
    "/thread/{thread_id}/messages/{message_id}", status_code=201,
    summary="Редактировать сообщение"
)
async def update_message(
        thread_id: int,
        message_id: str,
        body: NewMessageRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
):
    try:
        result = await service.update_or_delete_message(
            thread_id, message_id, user.id, body.content
        )
        return JSONResponse(
            content={
                "success": result,
            }, status_code=201
        )
    except ThreadException as e:
        raise BadRequestApiException(str(e))
    except (MessageNotFoundException, ThreadNotFoundException) as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/thread/{thread_id}/messages/{message_id}", status_code=201,
    summary="Удалить сообщение"
)
async def delete_message(
        thread_id: int,
        message_id: str,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
):
    try:
        result = await service.update_or_delete_message(
            thread_id, message_id, user.id, content=None,
            _type="del"
        )
        return JSONResponse(
            content={
                "success": result,
            }, status_code=201
        )
    except ThreadException as e:
        raise BadRequestApiException(str(e))
    except (MessageNotFoundException, ThreadNotFoundException) as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/thread/{thread_id}/messages/mark-as-read", status_code=201,
    summary="Отметить как прочитанное несколько сообщений"
)
async def mark_as_read(
        thread_id: int,
        body: MarkAsReadRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
):
    try:
        result = await service.mark_as_read(
            thread_id, body.ids, user.id
        )
        return JSONResponse(
            content={
                "success": result,
            }, status_code=201
        )
    except ThreadException as e:
        raise BadRequestApiException(str(e))
    except (MessageNotFoundException, ThreadNotFoundException) as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/unread/total", summary="Количество не прочитанных сообщений",
    status_code=200
)
async def get_unread_total(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
):
    try:
        result = await service.unread_message_quantity(user.id)
        return JSONResponse(
            content={
                "count": result
            }, status_code=200
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/threads", summary="Все диалоги",
    status_code=200
)
async def get_threads(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: MessagesService = Depends(get_messages_service),
):
    try:
        result = await service.get_user_threads(user.id)
        return JSONResponse(
            content={
                "threads": result
            }, status_code=200
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))