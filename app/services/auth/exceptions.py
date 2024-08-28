

class WrongTokenException(Exception):
    def __init__(self, reason):
        super().__init__(reason)


class OverdueTokenException(WrongTokenException):
    def __init__(self):
        super().__init__("Токен просрочен")


class DamagedTokenException(WrongTokenException):
    def __init__(self):
        super().__init__("Токен поврежден")


class BadCredentialsException(Exception):
    def __init__(self):
        super().__init__(
            "Не правильный логин или пароль"
        )


class BlockedUserException(Exception):
    def __init__(self):
        super().__init__(
            "Вы были заблокированы. Свяжитесь с поддержкой. Мы уверены, что это какая-то ошибка"
        )
