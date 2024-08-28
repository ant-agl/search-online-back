

class UserNotFoundException(Exception):
    def __init__(self):
        super().__init__('Пользователь не найден')


class AssertionUserReviewException(Exception):
    def __init__(self, message: str):
        super().__init__(
            message
        )


class ReviewException(Exception):
    def __init__(self, message: str):
        super().__init__(
            message
        )


class ReviewNotFoundException(Exception):
    def __init__(self, review_id: int):
        super().__init__(
            f"Отзыв({review_id}) не найден"
        )


class AlreadySellerException(Exception):
    def __init__(self):
        super().__init__(
            "Вы уже являетесь продавцом"
        )


class SelfReportException(Exception):
    def __init__(self):
        super().__init__(
            "Нельзя отправить жалобу на самого себя"
        )