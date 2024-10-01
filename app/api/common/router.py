import logging
from typing import Union, Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import create_model, BaseModel, Field

from app.api.common.requests import CreateCategory, TechnicalRequest
from app.api.common.responses import GetCities, GetCategoryTree, FAQSResponse
from app.api.dependencies import get_common_service
from app.api.exceptions import InternalServerError, ErrorResponse, ForbiddenApiException, BadRequestApiException, \
    NotFoundApiException
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.common.exceptions import ExceedingMaxDepth
from app.services.common.service import CommonService
from app.services.users.exceptions import UserNotFoundException
from app.utils.types import ItemType, success_response, status_response

router = APIRouter(
    prefix="/common",
)

logger = logging.getLogger("CommonRouter")


@router.get(
    "/cities", status_code=200,
    summary="Список всех активных городов"
)
async def get_cities(
        q: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        service: CommonService = Depends(get_common_service),
) -> GetCities:
    try:
        response = await service.get_all(
            q, offset, limit
        )
        return GetCities(
            result=response
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get(
    "/category/tree", status_code=200,
    response_model=Union[GetCategoryTree, ErrorResponse],
    summary="Дерево категорий"
)
async def get_category_tree(
        t: ItemType,
        service: CommonService = Depends(get_common_service),
) -> GetCategoryTree:
    try:
        return GetCategoryTree(
            result=await service.get_category_tree(t, on_moderating=False)
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/category", status_code=201,
    summary="Создать категорию"
)
async def create_category(
        body: CreateCategory,
        _: TokenPayload = Depends(Authenticator.get_current_user),
        service: CommonService = Depends(get_common_service),
):
    try:
        result = await service.create_new_category(body)
        return JSONResponse(
            content={
                "success": True,
                "data": result
            }, status_code=201
        )
    except ExceedingMaxDepth as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get("/category/{category_id}/status", status_code=200)
async def get_category_status(
        category_id: int,
        _: TokenPayload = Depends(Authenticator.get_current_user),
        service: CommonService = Depends(get_common_service),
) -> status_response:
    try:
        result = await service.get_new_category_status(category_id)
        return JSONResponse(
            content={
                "status": result
            }, status_code=200
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get("/faqs", status_code=200, summary="FAQs")
async def get_faqs(
        service: CommonService = Depends(get_common_service),
) -> FAQSResponse:
    try:
        return await service.get_faqs()
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/help", status_code=201,
    summary="Запрос в тех. поддержку"
)
async def help_request(
        body: TechnicalRequest,
        service: CommonService = Depends(get_common_service),
) -> success_response:
    try:
        result = await service.create_tech_support(body)
        return {
                "success": True,
            }
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
