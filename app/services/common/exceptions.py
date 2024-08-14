

class CityNotFoundException(Exception):
    def __init__(self, city_id):
        super().__init__(
            f"Город с ID: {city_id} не найден"
        )


class CityNotActiveException(Exception):
    def __init__(self, city_name):
        super().__init__(
            f"В городе {city_name} Найти.Онлайн еще не работает"
        )


class ExceedingMaxDepth(Exception):
    def __init__(self):
        super().__init__(
            "Выбранная родительская категория является максимальной подкатегорией"
        )
