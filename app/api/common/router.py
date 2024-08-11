import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.common.requests import CreateCategory
from app.api.common.responses import GetCities, GetCategoryTree
from app.api.dependencies import get_common_service
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.common.service import CommonService

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
    response_model=GetCategoryTree, summary="Дерево категорий"
)
async def get_category_tree(
        service: CommonService = Depends(get_common_service),
) -> GetCategoryTree:
    ...
    # TODO: После получения дерева категорий


@router.post(
    "/category", status_code=200,
    summary="Создать категорию"
)
async def create_category(
        body: CreateCategory,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: CommonService = Depends(get_common_service),
):
    ...
