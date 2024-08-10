
class UserAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("Пользователь с таким email уже существует")


class UserNotFoundException(Exception):
    def __init__(self, user_id: int = None):
        err = "Пользователь не существует"
        if user_id is not None:
            err += f" ID: {user_id}"
        super().__init__(err)
