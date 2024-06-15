from enum import Enum


class Gender(Enum):
    male = "male"
    female = "female"


class LocationType(Enum):
    current = "current"
    birth = "birth"


class PromocodeStatus(Enum):
    activated = "Активирован"
    not_activated = "Не активирован"


class ImageWideElementsPositions(Enum):
    BACKGROUND_IMAGE_PATH = 'images/backgrounds/wide_purple_background.jpg'

    DATE_TEXT = (600, 500)
    NAME_TEXT = (315, 205)

    START_MOON_SIGN_IMAGE = (175, 140)
    FIRST_MOON_SIGN_CAPTION = (175, 240)

    END_MOON_SIGN_IMAGE = (175, 400)
    SECOND_MOON_SIGN_CAPTION = (175, 520)

    MOON_PHASE = (990, 140)
    MOON_PHASE_CAPTION = (990, 320)


class ImageHighElementsPositions(Enum):  # TODO
    BACKGROUND_IMAGE_PATH = 'images/backgrounds/high_purple.jpg'

    DATE_TEXT = (600, 533)
    NAME_TEXT = (315, 205)

    START_MOON_SIGN_IMAGE = (175, 185)
    FIRST_MOON_SIGN_CAPTION = (175, 285)

    END_MOON_SIGN_IMAGE = (175, 445)
    SECOND_MOON_SIGN_CAPTION = (175, 565)

    MOON_PHASE = (990, 185)
    MOON_PHASE_CAPTION = (990, 365)

    BLANK_MOON = (600, 670)


class Align(Enum):
    CENTER = "center"


class FileFormat(Enum):
    JPEG = "JPEG"


class MoonSignInterpretationType(Enum):
    GENERAL = "general"
    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"


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
    MOON_SIGN = "moon_sign.jpeg"
    PREDICTION = "prediction.jpeg"


class ZodiacSign(Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


class SwissEphPlanet(int, Enum):
    SUN = 0
    MOON = 1
    MERCURY = 2
    VENUS = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6
    URANUS = 7
    NEPTUNE = 8
    PLUTO = 9


class Planets(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"
    ERIS = "Eris"


class PaymentStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class GeneralPredictionType(Enum):
    month = "month"
    week = "week"
    day = "day"


class PaymentMethod(Enum):
    YOOKASSA = "yookassa"
    PRODAMUS = "PRODAMUS"
