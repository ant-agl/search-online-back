
class UserAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("Пользователь с таким email уже существует")


class UserNotFoundException(Exception):
    def __init__(self):
        super().__init__("Пользователь не существует")
