import asyncio
import logging
from typing import Union

from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks, Query
from starlette.responses import JSONResponse

from app.api.dependencies import get_items_service, get_common_service, get_cloud_service, get_offers_service
from app.api.exceptions import ForbiddenApiException, UnprocessableApiException, InternalServerError, \
    NotFoundApiException, BadRequestApiException, ErrorResponse
from app.api.v1.items.requests import CreateItem, UpdateItem, GetCards
from app.api.v1.items.responses import GetItemsResponse, Meta, GetItemResponse, GetItemResponseSeller, PriceResponse, \
    LocationResponse, ItemPhotosResponse, ProductionTimeResponse, SellerResponse
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.cloud_service import CloudService
from app.services.common.exceptions import CategoryNotFoundException, CityNotFoundException, CityNotActiveException
from app.services.common.service import CommonService
from app.services.items.exceptions import MinPriceOverMaxPriceException, CategoryDisabledException, \
    CategoryOnModeratingException, ItemNotFoundException, PhotoNotFoundException
from app.services.items.service import ItemsService
from app.services.offers.service import OffersService
from app.utils.types import ItemType

router = APIRouter(
    prefix="/items"
)

logger = logging.getLogger("ItemsRouter")


@router.post(
    "/cards", summary="Все предложения",
    status_code=200, response_model=Union[GetItemsResponse, ErrorResponse],
    deprecated=True
)
async def get_items_pages(
        body: GetCards,
        page: int = Query(1, ge=1),
        page_limit: int = Query(50, ge=1, le=100),
        _: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        common_service: CommonService = Depends(get_common_service)
):
    ...


@router.get(
    "/cards/my", summary="Все услуги/товары продавца",
    status_code=200, response_model=Union[GetItemsResponse, ErrorResponse]
)
async def get_items_my_page(
        q: str = None,
        page: int = Query(1, ge=1),
        page_limit: int = Query(50, ge=1, le=100),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    user_id = user.id
    try:
        result, meta = await service.get_my_items(
            user_id, page, page_limit, q
        )
        return GetItemsResponse(
            items=result,
            meta=meta,
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/cards/my/{item_id}", summary="Услуга/товар продавца по ID",
    status_code=200, response_model=Union[GetItemResponseSeller, ErrorResponse | dict]
)
async def get_items_my_page(
        item_id: int,
        offer_page: int = Query(1, ge=1),
        offer_limit: int = Query(5, ge=1, le=10),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        offers_service: OffersService = Depends(get_offers_service),
):
    try:
        item = service.get_item_by_id(item_id, user.id)
        offers = offers_service.get_offers_by_criteria(
            {
                "item_id": item_id, "status": "PENDING"
            }, offer_page, offer_limit, exclude=["item"]
        )
        item, offers = await asyncio.gather(
            item, offers
        )
        return GetItemResponseSeller(
            id=item.id,
            title=item.title,
            type=item.type,
            description=item.description,
            status=item.status,
            price=PriceResponse(
                fix_price=item.price,
                from_price=item.from_price,
                to_price=item.to_price,
                currency=item.currency
            ),
            location=LocationResponse(
                city=item.city,
                address=item.address
            ),
            photos=[
                ItemPhotosResponse.model_validate(photo, from_attributes=True)
                for photo in item.photos
            ] if item.photos else [],
            seller=SellerResponse.model_validate(item.seller, from_attributes=True),
            production_time=ProductionTimeResponse(
                from_days=item.from_time,
                to_days=item.to_time,
            ),
            clicks=item.clicks,
            date_create=item.date_created,
            offers=offers[0],
            meta=offers[1]
        ).model_dump(exclude_none=True)
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except AssertionError:
        raise ForbiddenApiException(
            "Товар/услуга вам не принадлежит"
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/card/", summary="Добавление товара/услуги",
    status_code=201
)
async def create_new_item(
        body: CreateItem,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        common_service: CommonService = Depends(get_common_service)
):
    if not user.full_filled:
        raise UnprocessableApiException(
            "Для добавления товара или услуги профиль должен быть заполнен"
        )
    if "seller" not in user.types:
        raise ForbiddenApiException(
            "Создавать товары или услуги могут только продавцы"
        )
    try:
        result = await service.create_item(user.id, body, common_service)
        return JSONResponse(
            content=result,
        )
    except MinPriceOverMaxPriceException as e:
        raise UnprocessableApiException(str(e))
    except (CategoryNotFoundException, CityNotFoundException) as e:
        raise NotFoundApiException(str(e))
    except (
            CategoryDisabledException,
            CategoryOnModeratingException,
            CityNotActiveException
    ) as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/card/{item_id}", status_code=200,
    summary="Получение товара/услуги для покупателя",
    response_model=Union[GetItemResponse, ErrorResponse]
)
async def get_item_card(
        item_id: int,
        bg_task: BackgroundTasks,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    try:
        item = await service.get_item_by_id(item_id)
        bg_task.add_task(
            service.add_click, item_id, user.id
        )
        return GetItemResponse(
            id=item.id,
            title=item.title,
            type=item.type,
            description=item.description,
            status=item.status,
            price=PriceResponse(
                fix_price=item.price,
                from_price=item.from_price,
                to_price=item.to_price,
                currency=item.currency
            ),
            location=LocationResponse(
                city=item.city,
                address=item.address
            ),
            photos=[
                ItemPhotosResponse.model_validate(photo, from_attributes=True)
                for photo in item.photos
            ] if item.photos else [],
            seller=SellerResponse.model_validate(item.seller, from_attributes=True),
            production_time=ProductionTimeResponse(
                from_days=item.from_time,
                to_days=item.to_time,
            ),
            clicks=item.clicks,
            date_create=item.date_created,
        )
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/card/{item_id}", status_code=201,
    summary="Обновление товара/услуги", deprecated=True
)
async def update_item(
        item_id: int,
        body: UpdateItem,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    if not user.full_filled:
        raise UnprocessableApiException(
            "Для добавления товара или услуги профиль должен быть заполнен"
        )
    if "seller" not in user.types:
        raise ForbiddenApiException(
            "Создавать товары или услуги могут только продавцы"
        )
    try:
        result = await service.update_item(item_id, body)
        return JSONResponse(
            content=result,
            status_code=201
        )
    except MinPriceOverMaxPriceException as e:
        raise UnprocessableApiException(str(e))
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/photo/{item_id}", status_code=201,
    summary="Добавление фото товара/услуги"
)
async def add_item_photo(
        item_id: int,
        index: int,
        file: UploadFile,
        bg_tasks: BackgroundTasks,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        cloud_service: CloudService = Depends(get_cloud_service)
):
    if not user.full_filled:
        raise UnprocessableApiException(
            "Для добавления фото профиль должен быть заполнен"
        )
    if "seller" not in user.types:
        raise ForbiddenApiException(
            "Добавить фото могут только продавцы"
        )
    try:
        key = await service.add_photo(
            user.id, item_id, index, cloud_service.get_link
        )
        if key:
            await cloud_service.session()
            bg_tasks.add_task(
                cloud_service.save_file,
                await file.read(),
                key
            )
        return JSONResponse(
            content={
                "success": True
            }, status_code=201
        )
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except AssertionError:
        raise ForbiddenApiException(
            "Вы не можете добавить фото к товару/услуге, "
            "которая вам не принадлежит"
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/photo/{item_id}/{photo_id}", summary="Удаление фото",
    status_code=204
)
async def remove_item_photo(
        item_id: int,
        photo_id: int,
        bg_tasks: BackgroundTasks,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        cloud_service: CloudService = Depends(get_cloud_service)
):
    if "seller" not in user.types:
        raise ForbiddenApiException(
            "Добавить фото могут только продавцы"
        )
    try:
        key = await service.delete_photo(user.id, item_id, photo_id)
        bg_tasks.add_task(
            cloud_service.delete_file,
            key
        )
    except (ItemNotFoundException, PhotoNotFoundException) as e:
        raise NotFoundApiException(str(e))
    except AssertionError:
        raise ForbiddenApiException(
            "Вы не можете удалить фото товара/услуги, "
            "которая вам не принадлежит"
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/card/{item_id}", summary="Удаление товара/услуги",
    status_code=204
)
async def delete_item(
        item_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    if "seller" not in user.types:
        raise ForbiddenApiException(
            "Удалять товары или услуги могут только продавцы"
        )

    try:
        result = await service.delete_item(user.id, item_id)
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except AssertionError:
        raise ForbiddenApiException(
            "Вы не можете удалить товар/услугу, которая вам не принадлежит"
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/card/{item_id}/reviews", status_code=201,
    summary="Оставить отзыв о товаре/услуге", deprecated=True
)
async def create_item_review():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/card/{item_id}/reviews", status_code=201,
    summary="Посмотреть отзывы о товаре/услуге", deprecated=True
)
async def create_item_review():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/card/{item_id}/reviews/{review_id}", status_code=201,
    summary="Удалить отзыв о товаре/услуге", deprecated=True
)
async def create_item_review():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))