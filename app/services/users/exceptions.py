

class UserNotFoundException(Exception):
    def __init__(self):
        super().__init__('Пользователь не найден')
