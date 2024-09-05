

class ThreadAlreadyExists(Exception):
    def __init__(self):
        super().__init__("Диалог уже создан")


class ThreadException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ThreadNotFoundException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        

class MessageNotFoundException(Exception):
    def __init__(self, message: str):
        super().__init__(message)