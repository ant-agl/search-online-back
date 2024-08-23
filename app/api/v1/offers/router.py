import logging

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from starlette.responses import JSONResponse

from app.api.dependencies import get_offers_service, get_user_service, get_items_service
from app.api.exceptions import InternalServerError, BadRequestApiException, NotFoundApiException, ForbiddenApiException
from app.api.v1.offers.requests import CreateOffer, UpdateOfferStatus, UpdateOfferDetails
from app.api.v1.offers.responses import GetOffersResponse
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.items.service import ItemsService
from app.services.offers.exceptions import WrongOfferSenderException, ItemHasAnotherOwnerException, \
    WrongOfferReceiverException, SelfOfferException, DeleteOfferException, OfferNotFoundException, \
    OfferNotBelongYouException, WrongNewStatus, OfferAlreadyClosed, UpdateStatusException
from app.services.offers.service import OffersService
from app.services.users.exceptions import UserNotFoundException
from app.services.users.service import UserService
from app.utils.types import OffersTypes

router = APIRouter(
    prefix="/offers",
    tags=["Предложения"],
)
logger = logging.getLogger("OffersRouter")


@router.post(
    "/new", summary="Создать заказ",
    status_code=201
)
async def create_offer(
        body: CreateOffer,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: OffersService = Depends(get_offers_service),
        users_service: UserService = Depends(get_user_service),
        items_service: ItemsService = Depends(get_items_service),
):
    try:
        offer_id = await service.create(
            user, body, users_service,
            items_service
        )
        # TODO: Добавить отправку уведомлений
        return JSONResponse(
            content={
                "success": True,
                "offer_id": offer_id
            }, status_code=201
        )
    except (
            WrongOfferSenderException, ItemHasAnotherOwnerException,
            WrongOfferReceiverException, SelfOfferException
    ) as e:
        raise BadRequestApiException(str(e))
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/{offer_id}", status_code=200,
    summary="Получить заказ по ID"
)
async def get_offer(
        offer_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: OffersService = Depends(get_offers_service)
):
    try:
        offer = await service.get_offer_by_id(offer_id, user.id)
        return offer
    except OfferNotFoundException as e:
        raise NotFoundApiException(str(e))
    except OfferNotBelongYouException as e:
        raise ForbiddenApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/", status_code=200,
    summary="Получить все заказы"
)
async def get_all_offers(
        target: OffersTypes,
        page: int = Query(1, ge=1),
        page_limit: int = Query(50, ge=1, le=100),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: OffersService = Depends(get_offers_service),
        users_service: UserService = Depends(get_user_service),
        items_service: ItemsService = Depends(get_items_service),
):
    try:
        result, meta = await service.get_offers(
            user.id, target.value, users_service, items_service,
            page, page_limit
        )
        return GetOffersResponse(
            result=result,
            meta=meta
        ).model_dump(exclude_none=True)

    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/{offer_id}", status_code=204,
    summary="Удалить заказ пользователя"
)
async def delete_offer(
        offer_id: int,
        bg_tasks: BackgroundTasks,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: OffersService = Depends(get_offers_service),
):
    try:
        receiver = await service.delete_offer(offer_id, user.id)
        # bg_tasks.add_task() TODO: Добавить оповещение второго челика
    except OfferNotFoundException as e:
        raise NotFoundApiException(str(e))
    except DeleteOfferException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/{offer_id}/details/", summary="Изменить детали заказа",
    status_code=200
)
async def update_offer(
        offer_id: int,
        body: UpdateOfferDetails,
        bg_tasks: BackgroundTasks,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: OffersService = Depends(get_offers_service)
):
    try:
        receiver = await service.update_offer_details(
            offer_id, user.id, body
        )
        # bg_tasks.add_task() TODO: Добавить оповещалку
        return JSONResponse(
            content={
                "success": True,
            }, status_code=200
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.put(
    "/{offer_id}/status", summary="Изменить статус заказа",
    status_code=201
)
async def update_offer_status(
        offer_id: int,
        body: UpdateOfferStatus,
        bg_tasks: BackgroundTasks,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: OffersService = Depends(get_offers_service)
):
    try:
        receiver = await service.update_offer_status(offer_id, user.id, body)
        # bg_tasks.add_task() TODO: Добавить оповещалку
        return JSONResponse(
            content={
                "success": True,
            }, status_code=200
        )
    except (WrongNewStatus, OfferAlreadyClosed, UpdateStatusException) as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
