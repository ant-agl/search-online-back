from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Модель ответа, при возникновении ошибки.

    Поля:
        - success(bool): Состояние запроса.
        - error(str): Описание ошибки.
        - status(int): Статус ответа.
    """
    success: bool
    error: str
    status: int
    message: str | None = None


class BaseApiException(Exception):
    """
    Базовый класс ошибок от сервера

    Аргументы для инициализации:
        success(bool) - Успешность запроса
        error(str) - Описание ошибки
        status_code(int) - Статус ответа
    """
    def __init__(self, success: bool, error: str, status_code: int, message: str = None):
        self.success = success
        self.error = error
        self.status_code = status_code
        self.message = message


class BadRequestApiException(BaseApiException):
    def __init__(self, message: str = None):
        super().__init__(
            success=False,
            error="Bad Request",
            status_code=400,
            message=message
        )


class UnauthorizedApiException(BaseApiException):
    """
    Наследник базового класса исключений сервера.
    Используется для ошибки авторизации.
    """
    def __init__(self, message: str = None):
        super().__init__(
            success=False,
            error="Unauthorized",
            status_code=401,
            message=message
        )


class ForbiddenApiException(BaseApiException):
    """
    Наследник базового класса исключений сервера.
    Используется для запрета доступа.
    """
    def __init__(self, message: str = None):
        super().__init__(
            success=False,
            error="Forbidden",
            status_code=403,
            message=message
        )


class NotFoundApiException(BaseApiException):
    """
    Наследник базового класса исключений сервера.
    Используется для ошибки авторизации.
    """
    def __init__(self, message: str = None):
        super().__init__(
            success=False,
            error="Not Found",
            status_code=404,
            message=message
        )


class UnprocessableApiException(BaseApiException):
    """
    Наследник базового класса исключений сервера.
    Используется для ошибки входных данных.
    """
    def __init__(self, message: str = None):
        super().__init__(
            error="Unprocessable entity",
            success=False,
            status_code=422,
            message=message
        )


class LockedApiException(BaseApiException):
    def __init__(self, message: str = None):
        super().__init__(
            error="Locked",
            success=False,
            status_code=423,
            message=message
        )


class TokenExpiredApiException(BaseApiException):
    def __init__(self, message: str = None):
        super().__init__(
            status_code=493,
            error="Token expired/invalid",
            success=False,
            message=message
        )


class InternalServerError(BaseApiException):
    """
    Наследник базового класса исключений сервера.
    Используется для ошибки внутри сервера.
    """
    def __init__(self, message: str = None):
        super().__init__(
            success=False,
            error=f"InternalServerError",
            status_code=500,
            message=message
        )
