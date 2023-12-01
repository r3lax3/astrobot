from enum import Enum

class Gender(Enum):
    male = 'male'
    female = 'female'


class LocationType(Enum):
    current = 'current'
    birth = 'birth'


class PromocodeStatus(Enum):
    activated = "Активирован"
    not_activated = "Не активирован"

