from app.utils.types import STATUS_MAP


class WrongOfferReceiverException(Exception):
    def __init__(self):
        super().__init__("Получатель заказа не является продавцом")


class WrongOfferSenderException(Exception):
    def __init__(self):
        super().__init__("На запрос может отвечать только продавец")


class ItemHasAnotherOwnerException(Exception):
    def __init__(self):
        super().__init__("Данная услуга/товар принадлежит другому продавцу")


class SelfOfferException(Exception):
    def __init__(self):
        super().__init__("Нельзя сделать заказ самому себе")


class DeleteOfferException(Exception):
    def __init__(self):
        super().__init__(
            "Вы не можете удалить заказ, который не создавали"
        )


class OfferNotFoundException(Exception):
    def __init__(self, offer_id: int):
        super().__init__(
            f"Заказ {offer_id} не найден"
        )


class OfferNotBelongYouException(Exception):
    def __init__(self, offer_id: int):
        super().__init__(
            f"Заказ {offer_id} вам не принадлежит"
        )


class WrongNewStatus(Exception):
    def __init__(self, offer_id: int, new_status: str, old_status: str):
        super().__init__(
            f"Невозможно приметь статус {STATUS_MAP[new_status]} "
            f"для заказа с id {offer_id}, "
            f"так как он находится в статусе {STATUS_MAP[old_status]}"
        )


class OfferAlreadyClosed(Exception):
    def __init__(self, offer_id: int):
        super().__init__(
            f"Заказ {offer_id} уже завершен или отменен"
        )


class UpdateOfferStatusException(Exception):
    def __init__(self, offer_id: int, status: str):
        super().__init__(
            f"Вы не можете изменить статус заказа({offer_id}) на {STATUS_MAP[status]}"
        )


class UpdateStatusException(Exception):
    def __init__(self, message):
        super().__init__(message)
