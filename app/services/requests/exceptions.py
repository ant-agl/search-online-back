

class CreateRequestException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class RequestException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class RequestNotFound(Exception):
    def __init__(self, request_id: int):
        super().__init__(
            f"Запрос({request_id}) не найден"
        )
