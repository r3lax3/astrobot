import io
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src import config
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.enums import Align, FileFormat, MoonPhase, PILPositions, ZodiacSign
from src.translations import ZODIAC_RU_TRANSLATION

# Get the date format from the configuration
DATE_FORMAT: str = config.get("database.date_format")
BACKGROUND_IMAGE_PATH = "images/backgrounds/purple_background.jpg"
DATE_TEXT_POSITION = (404, 450)  # Подганял чётко под изображение методом тыка
COLOR_WHITE = "#ffffff"
FONT_PATH = "fonts/Comic Sans MS.ttf"
DATE_FONT_SIZE = 80
TEXT_FONT_SIZE = 32

DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
TIME_FORMAT: str = config.get("database.time_format")

MOON_IN_SIGNS_INTERPRETATIONS = get_moon_in_signs_interpretations()

DATE_FONT = ImageFont.truetype(FONT_PATH, DATE_FONT_SIZE)
TEXT_FONT = ImageFont.truetype(FONT_PATH, TEXT_FONT_SIZE)


def zodiac_sign_translate_to_russian(sign_str: ZodiacSign):
    return ZODIAC_RU_TRANSLATION.get(sign_str, "Неизвестный знак")


def calculate_adjust_for_centering(
    coordinates: tuple[int, int],
    obj: str | Image.Image,
    font: Optional[ImageFont.FreeTypeFont] = None,
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
        dummy_image = Image.new("RGB", (0, 0))
        drawer = ImageDraw.Draw(dummy_image)

        # get text size
        _, _, w, h = drawer.textbbox((0, 0), obj, font=font, align=Align.CENTER.value)

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
    moon_phase_caption: Optional[str] = None,
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
                PILPositions.DATE_TEXT.value, date, DATE_FONT
            ),  # text size-adjusted position
            date,
            fill=COLOR_WHITE,
            font=DATE_FONT,
            align=Align.CENTER.value,
        )

    if start_sign is not None:
        first_sign_image = Image.open(f"images/moon_signs/{start_sign.value}.png")
        first_sign_position = calculate_adjust_for_centering(
            PILPositions.START_MOON_SIGN_IMAGE.value, first_sign_image
        )

        background_image.paste(first_sign_image, first_sign_position, first_sign_image)

        first_sign_caption = f"Луна в {zodiac_sign_translate_to_russian(start_sign)}"

        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.FIRST_MOON_SIGN_CAPTION.value,
                first_sign_caption,
                TEXT_FONT,
            ),  # centered coordinates
            first_sign_caption,
            fill=COLOR_WHITE,
            font=TEXT_FONT,
            align=Align.CENTER.value,
        )

    # If an end sign is given, load and paste
    if change_time is not None and end_sign is not None:
        end_sign_image = Image.open(f"images/moon_signs/{end_sign.value}.png")
        end_sign_position = calculate_adjust_for_centering(
            PILPositions.END_MOON_SIGN_IMAGE.value, end_sign_image
        )

        background_image.paste(end_sign_image, end_sign_position, end_sign_image)

        second_sign_caption = (
            f"c {change_time} Луна\nв {zodiac_sign_translate_to_russian(end_sign)}"
        )

        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.SECOND_MOON_SIGN_CAPTION.value,
                second_sign_caption,
                TEXT_FONT,
            ),  # text size-adjusted position
            second_sign_caption,
            fill=COLOR_WHITE,
            font=TEXT_FONT,
            align=Align.CENTER.value,
        )

    if moon_phase is not None:
        moon_phase_image = Image.open(f"images/moon_phases/{moon_phase.value}.png")
        moon_phase_position = calculate_adjust_for_centering(
            PILPositions.MOON_PHASE.value, moon_phase_image
        )

        background_image.paste(moon_phase_image, moon_phase_position, moon_phase_image)

    if moon_phase_caption is not None:
        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.MOON_PHASE_CAPTION.value, moon_phase_caption, TEXT_FONT
            ),  # text size-adjusted position
            moon_phase_caption,
            fill=COLOR_WHITE,
            font=TEXT_FONT,
            align=Align.CENTER.value,
        )

    # Save or return the image
    byte_array = io.BytesIO()
    background_image.save(byte_array, format=FileFormat.JPEG.value)
    return byte_array.getvalue()
