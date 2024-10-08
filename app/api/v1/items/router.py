import asyncio
import logging
from typing import Union, Annotated

from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks, Query
from pydantic import create_model, Field, BaseModel
from starlette.responses import JSONResponse

from app.api.dependencies import get_items_service, get_common_service, get_cloud_service, get_offers_service, \
    get_user_service
from app.api.exceptions import ForbiddenApiException, UnprocessableApiException, InternalServerError, \
    NotFoundApiException, BadRequestApiException, ErrorResponse
from app.api.v1.items.requests import CreateItem, UpdateItem, GetCards, PostItemReview
from app.api.v1.items.responses import GetItemsResponse, Meta, GetItemResponse, GetItemResponseSeller, PriceResponse, \
    LocationResponse, ItemPhotosResponse, ProductionTimeResponse, SellerResponse
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.cloud_service import CloudService
from app.services.common.exceptions import CategoryNotFoundException, CityNotFoundException, CityNotActiveException
from app.services.common.service import CommonService
from app.services.items.exceptions import MinPriceOverMaxPriceException, CategoryDisabledException, \
    CategoryOnModeratingException, ItemNotFoundException, PhotoNotFoundException, ItemException
from app.services.items.service import ItemsService
from app.services.offers.service import OffersService
from app.services.users.service import UserService
from app.utils.types import ItemType, success_response

router = APIRouter(
    prefix="/items"
)

logger = logging.getLogger("ItemsRouter")


@router.post(
    "/cards", summary="Все предложения",
    status_code=200, response_model=Union[GetItemsResponse, ErrorResponse],
)
async def get_items_pages(
        body: GetCards,
        page: int = Query(1, ge=1),
        page_limit: int = Query(50, ge=1, le=100),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        user_service: UserService = Depends(get_user_service)
):
    try:
        result = await service.get_filtered_items(
            body, page, page_limit, user.id, user_service
        )
        return result
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


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
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    try:
        item = await service.get_item_by_id(item_id, user.id)
        return GetItemResponseSeller(
            id=item.id,
            title=item.title,
            type=item.type,
            description=item.description,
            status=item.status,
            price=PriceResponse(
                fix_price=item.fix_price,
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
            rating=item.rating,
            reviews_quantity=item.reviews_quantity,
            offers=[],
            meta=None
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


@router.get(
    "/cards/my/{item_id}/offers", status_code=200,
    summary="Получить запросы на товары"
)
async def get_offers_pages(
        item_id: int,
        offer_page: int = Query(1, ge=1),
        offer_limit: int = Query(5, ge=1, le=10),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
        offers_service: OffersService = Depends(get_offers_service),
):
    try:
        await service.get_item_owner(item_id, user.id)
        offers, meta = await offers_service.get_offers_by_criteria(
            {
                "item_id": item_id, "status": "PENDING"
            }, offer_page, offer_limit, exclude=["item"]
        )
        return {
            "offers": offers,
            "meta": meta,
        }
    except ItemException as e:
        raise ForbiddenApiException(str(e))
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
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
) -> Annotated[
    dict, create_model(
        "CreateItemResponse",
        id=Annotated[int, Field(...)],
        status=Annotated[str, Field(...)], __base__=BaseModel
    )
]:
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
        return result
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
                fix_price=item.fix_price,
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
            rating=item.rating,
            reviews_quantity=item.reviews_quantity,
            date_create=item.date_created,

        )
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/card/{item_id}", status_code=204,
    summary="Обновление товара/услуги"
)
async def update_item(
        item_id: int,
        body: UpdateItem,
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
        await service.update_item(
            user.id, item_id, body, common_service
        )
    except MinPriceOverMaxPriceException as e:
        raise UnprocessableApiException(str(e))
    except (
            ItemNotFoundException, CityNotFoundException,
            CategoryNotFoundException
    ) as e:
        raise NotFoundApiException(str(e))
    except (
            ItemException, CityNotActiveException,
            CategoryDisabledException, CategoryOnModeratingException
    ) as e:
        raise BadRequestApiException(str(e))
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
) -> success_response:
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
    summary="Оставить отзыв о товаре/услуге"
)
async def create_item_review(
        item_id: int,
        body: PostItemReview,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
) -> success_response:
    try:
        result = await service.add_review(user.id, item_id, body)
        return JSONResponse(
            content={
                "success": result
            }, status_code=201
        )
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except ItemException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/card/{item_id}/reviews", status_code=200,
    summary="Посмотреть отзывы о товаре/услуге",
)
async def create_item_review(
        item_id: int,
        page: int = Query(1, ge=1),
        page_limit: int = Query(50, ge=1, le=100),
        by_stars: int = None,
        _: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    try:
        return await service.get_reviews(
            item_id, page, page_limit, by_stars
        )
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except ItemException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/card/{item_id}/reviews/{review_id}", status_code=204,
    summary="Удалить отзыв о товаре/услуге",
)
async def create_item_review(
        item_id: int,
        review_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: ItemsService = Depends(get_items_service),
):
    try:
        await service.delete_review(item_id, user.id, review_id)
    except ItemNotFoundException as e:
        raise NotFoundApiException(str(e))
    except ItemException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
