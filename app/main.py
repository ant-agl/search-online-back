from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.api.auth.router import router as auth_router
from app.api.exceptions import BaseApiException
from app.api.v1.users.router import router as users_router
from app.api.v1.items.router import router as items_router
from app.api.v1.offers.router import router as offers_router
from app.api.common.router import router as common_router
from app.repository.models import create_tables
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.setup_architecture()
    settings.setup_logging()
    await create_tables()
    yield


app = FastAPI(
    **settings.app_config,
    lifespan=lifespan
)

root_router = APIRouter(
    prefix="/api/v1",
)
root_router.include_router(users_router, tags=["Пользователи"])
root_router.include_router(items_router, tags=["Товары/услуги"])
root_router.include_router(offers_router, tags=["Предложения"])


app.include_router(common_router, tags=["Общее"])
app.include_router(auth_router, tags=["Авторизация, аутентификация, восстановление"])
app.include_router(root_router)


@app.exception_handler(BaseApiException)
async def api_exception_handler(
        request: Request, exc: BaseApiException
) -> JSONResponse:
    """
    Регистрация обработчика класса ошибок для кастомизации тела ответа

    Аргументы:
        request(Requests) - Объект с метаданными о запросе
        exc(BaseApiException): Класс или класс наследник ошибок сервера

    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": exc.success,
            "error": exc.error,
            "status": exc.status_code,
            "message": exc.message
        }
    )


@app.get("/", tags=["Документация"])
async def root():
    return RedirectResponse(url="/docs", status_code=308)


@app.get("/health", tags=["Проверка состояния"])
async def health():
    return JSONResponse({"status": "ok"}, status_code=200)
