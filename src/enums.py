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


class PILPositions(Enum):
    DATE_TEXT = (600, 500)
    START_MOON_SIGN_IMAGE = (175, 140)
    FIRST_MOON_SIGN_CAPTION = (175, 240)
    END_MOON_SIGN_IMAGE = (175, 400)
    SECOND_MOON_SIGN_CAPTION = (175, 515)
    MOON_PHASE = (990, 175)
    MOON_PHASE_CAPTION = (990, 375)


class Align(Enum):
    CENTER = 'center'


class FileFormat(Enum):
    JPEG = "JPEG"


class MoonSignInterpretationType(Enum):
    GENERAL = "general"
    FAVORABLE = 'favorable'
    UNFAVORABLE = 'unfavorable'


class MoonPhase(Enum):
    NEW_MOON = "New Moon"
    WAXING_CRESCENT = "Waxing Crescent"
    FIRST_QUARTER = "First Quarter"
    WAXING_GIBBOUS = "Waxing Gibbous"
    FULL_MOON = "Full Moon"
    WANING_GIBBOUS = "Waning Gibbous"
    LAST_QUARTER = "Last Quarter"
    WANING_CRESCENT = "Waning Crescent"

    
class FileName(Enum):
    moon_sign = 'moon_sign.jpeg'

