

class MinPriceOverMaxPriceException(Exception):
    def __init__(self):
        super().__init__(
            "Минимальная цена превышает максимальную."
        )


class CategoryOnModeratingException(Exception):
    def __init__(self, category_name: str):
        super().__init__(
            f"Категория '{category_name}' на модерации"
        )


class CategoryDisabledException(Exception):
    def __init__(self, category_name: str):
        super().__init__(
            f"Категория '{category_name}' не активна"
        )


class ItemNotFoundException(Exception):
    def __init__(self, item_id: int):
        super().__init__(
            f"Объект с ID: {item_id} не найден"
        )


class PhotoNotFoundException(Exception):
    def __init__(self):
        super().__init__(
            "Фото не найдено"
        )


class ItemException(BaseException):
    def __init__(self, message: str):
        super().__init__(message)
        