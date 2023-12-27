import io

from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from enum import Enum

class PILPositions(Enum):
    DATE_TEXT = (600, 500)
    START_MOON_SIGN_IMAGE = (175, 140)
    FIRST_MOON_SIGN_CAPTION = (175, 240)
    END_MOON_SIGN_IMAGE = (175, 400)
    SECOND_MOON_SIGN_CAPTION = (175, 520)
    MOON_PHASE = (990, 140)
    MOON_PHASE_CAPTION = (990, 290)

class Align(Enum):
    CENTER = 'center'

class FileFormat(Enum):
    JPEG = "JPEG"

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
    MOON_SIGN = 'moon_sign.jpeg'
    PREDICTION = 'prediction.jpeg'

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

class SwissEphPlanet(Enum):
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

class PaymentStatus(Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'


# TRANSLATIONS
ZODIAC_RU_TRANSLATION = {
    ZodiacSign.ARIES: "Овне",
    ZodiacSign.TAURUS: "Тельце",
    ZodiacSign.GEMINI: "Близнецах",
    ZodiacSign.CANCER: "Раке",
    ZodiacSign.LEO: "Льве",
    ZodiacSign.VIRGO: "Деве",
    ZodiacSign.LIBRA: "Весах",
    ZodiacSign.SCORPIO: "Скорпионе",
    ZodiacSign.SAGITTARIUS: "Стрельце",
    ZodiacSign.CAPRICORN: "Козероге",
    ZodiacSign.AQUARIUS: "Водолее",
    ZodiacSign.PISCES: "Рыбах"
}
MOON_PHASE_RU_TRANSLATIONS = {
    MoonPhase.NEW_MOON: "НОВОЛУНИЕ",
    MoonPhase.WAXING_CRESCENT: "РАСТУЩИЙ ПОЛУМЕСЯЦ",
    MoonPhase.FIRST_QUARTER: "ПЕРВАЯ ЧЕТВЕРТЬ",
    MoonPhase.WAXING_GIBBOUS: "РАСТУЩАЯ ЛУНА",
    MoonPhase.FULL_MOON: "ПОЛНОЛУНИЕ",
    MoonPhase.WANING_GIBBOUS: "УБЫВАЮЩАЯ ЛУНА",
    MoonPhase.LAST_QUARTER: "ПОСЛЕДНЯЯ ЧЕТВЕРТЬ",
    MoonPhase.WANING_CRESCENT: "УБЫВАЮЩИЙ ПОЛУМЕСЯЦ"
}

# Константы
SECONDS_IN_DAY = 24 * 60 * 60
ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
ZODIAC_SIGNS = [
    ZodiacSign.ARIES,
    ZodiacSign.TAURUS,
    ZodiacSign.GEMINI,
    ZodiacSign.CANCER,
    ZodiacSign.LEO,
    ZodiacSign.VIRGO,
    ZodiacSign.LIBRA,
    ZodiacSign.SCORPIO,
    ZodiacSign.SAGITTARIUS,
    ZodiacSign.CAPRICORN,
    ZodiacSign.AQUARIUS,
    ZodiacSign.PISCES
]

MOON_PHASES_RANGES = {
    (0, 0.01): MoonPhase.NEW_MOON,
    (0.05, 0.45): (MoonPhase.WAXING_CRESCENT, MoonPhase.WANING_CRESCENT),
    (0.45, 0.55): (MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER),
    (0.55, 0.99): (MoonPhase.WAXING_GIBBOUS, MoonPhase.WANING_GIBBOUS),
    (0.99, 1): MoonPhase.FULL_MOON,
}

# Get the date format from the configuration
BACKGROUND_IMAGE_PATH = 'images/backgrounds/purple_background.jpg'
COLOR_WHITE = '#ffffff'
FONT_PATH = "fonts/Comic Sans MS.ttf"

# FONT SIZE
DATE_FONT_SIZE = 80
TEXT_FONT_SIZE = 32 

# FORMATS
ISO_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"

# FONTS
DATE_FONT = ImageFont.truetype(FONT_PATH, DATE_FONT_SIZE)
TEXT_FONT = ImageFont.truetype(FONT_PATH, TEXT_FONT_SIZE)


def zodiac_sign_translate_to_russian(sign_str: ZodiacSign):
    return ZODIAC_RU_TRANSLATION.get(sign_str, "Неизвестный знак")


def calculate_adjust_for_centering(
    coordinates: tuple[int, int],
    obj: str | Image.Image,
    font: Optional[ImageFont.FreeTypeFont] = None
) -> tuple[int, int]:
    """
    Calculate the top-left coordinates to place an object (text or image) 
    at the center of given coordinates.
    
    :param coordinates: A tuple (x, y) representing the center coordinates 
    where the object should be placed.
    :param obj: A text string or a PIL Image to be centered.
    :return: A tuple (top_left_x, top_left_y) representing the top-left 
    coordinates to place the object.
    """
    if isinstance(obj, str):
        dummy_image = Image.new('RGB', (0, 0))
        drawer = ImageDraw.Draw(dummy_image)

        # get text size
        _, _, w, h = drawer.textbbox(
            (0, 0), 
            obj, 
            font=font,
            align=Align.CENTER.value
        )

    elif isinstance(obj, Image.Image):
        w, h = obj.size
    
    else:
        raise ValueError("Object must be a string or a PIL Image.")
    
    X, Y = coordinates 

    # Calculate top-left coordinates for centering
    x = int(X - w / 2)
    y = int(Y - h / 2)

    return (x, y)


def generate_image_with_astrodata(
    date: Optional[str] = None, 
    start_sign: Optional[ZodiacSign] = None,
    change_time: Optional[str] = None,
    end_sign: Optional[ZodiacSign] = None,
    moon_phase: Optional[MoonPhase] = None,
    moon_phase_caption: Optional[str] = None
) -> bytes:
    """
    Generates an image representing the transition of the Moon through astrological signs along with associated captions.

    This function creates a composite image based on the provided astrological information. The resulting image includes visual representations of the starting and ending Moon signs, the transition time, the Moon's phase, and associated captions.

    Parameters:
    - date (Optional[str]): The date to be displayed on the image. This should be a string in any preferred format.
    - start_sign (Optional[ZodiacSign]): The astrological sign where the Moon starts. This should be an instance of the `ZodiacSign` enum representing the sign.
    - change_time (Optional[str]): The time when the Moon transitions from the starting sign to the ending sign. Should be a string representing time.
    - end_sign (Optional[ZodiacSign]): The astrological sign where the Moon ends. This should be an instance of the `ZodiacSign` enum representing the sign.
    - moon_phase (Optional[MoonPhase]): The phase of the Moon. This should be an instance of the `MoonPhase` enum representing the lunar phase.
    - moon_phase_caption (Optional[str]): A caption describing the Moon phase. This should be a string.

    Returns:
    - bytes: The image data in bytes format. This can be directly used to write to a file or stream over a network.
    """
    # Open the background image
    background_image = Image.open(BACKGROUND_IMAGE_PATH)
    drawer = ImageDraw.Draw(background_image)
    
    if date is not None: 
        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.DATE_TEXT.value, 
                date, 
                DATE_FONT
            ),  # text size-adjusted position
            date, 
            fill=COLOR_WHITE, 
            font=DATE_FONT,
            align=Align.CENTER.value
        )

    if start_sign is not None:
        
        first_sign_image = Image.open(f'images/moon_signs/{start_sign.value}.png')
        first_sign_position = calculate_adjust_for_centering(
            PILPositions.START_MOON_SIGN_IMAGE.value, 
            first_sign_image
        )

        background_image.paste(
            first_sign_image, 
            first_sign_position,
            first_sign_image
        )

        first_sign_caption = f'Луна в {zodiac_sign_translate_to_russian(start_sign)}'
        
        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.FIRST_MOON_SIGN_CAPTION.value,
                first_sign_caption,
                TEXT_FONT
            ),  # centered coordinates
            first_sign_caption,
            fill=COLOR_WHITE, 
            font=TEXT_FONT,
            align=Align.CENTER.value
        )

    # If an end sign is given, load and paste 
    if change_time is not None and end_sign is not None:
        end_sign_image = Image.open(f'images/moon_signs/{end_sign.value}.png')
        end_sign_position = calculate_adjust_for_centering(
            PILPositions.END_MOON_SIGN_IMAGE.value,
            end_sign_image
        )

        background_image.paste(
            end_sign_image, 
            end_sign_position,
            end_sign_image
        )

        second_sign_caption = f'c {change_time} Луна\nв {zodiac_sign_translate_to_russian(end_sign)}'

        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.SECOND_MOON_SIGN_CAPTION.value,
                second_sign_caption,
                TEXT_FONT
            ),  # text size-adjusted position
            second_sign_caption,
            fill=COLOR_WHITE, 
            font=TEXT_FONT,
            align=Align.CENTER.value
        )

    if moon_phase is not None:
        moon_phase_image = Image.open(f'images/moon_phases/{moon_phase.value}.png')
        moon_phase_position = calculate_adjust_for_centering(
            PILPositions.MOON_PHASE.value,
            moon_phase_image
        )

        background_image.paste(
            moon_phase_image, 
            moon_phase_position,
            moon_phase_image
        )

    if moon_phase_caption is not None:
        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.MOON_PHASE_CAPTION.value,
                moon_phase_caption,
                TEXT_FONT
            ),  # text size-adjusted position
            moon_phase_caption,
            fill=COLOR_WHITE, 
            font=TEXT_FONT,
            align=Align.CENTER.value
        )

    # Save or return the image
    byte_array = io.BytesIO()
    background_image.save(byte_array, format=FileFormat.JPEG.value)
    return byte_array.getvalue()


ALL_MOON_PHASES = [
    MoonPhase.NEW_MOON,
    MoonPhase.WAXING_CRESCENT,
    MoonPhase.FIRST_QUARTER,
    MoonPhase.WAXING_GIBBOUS,
    MoonPhase.FULL_MOON,
    MoonPhase.WANING_GIBBOUS,
    MoonPhase.LAST_QUARTER,
    MoonPhase.WANING_CRESCENT
]


for moon_phase in ALL_MOON_PHASES:
    with open(
        f'tests/images/{moon_phase.value}, {MOON_PHASE_RU_TRANSLATIONS[moon_phase]}.jpeg', 
        "wb"
    ) as f:
        f.write(generate_image_with_astrodata(moon_phase=moon_phase))

