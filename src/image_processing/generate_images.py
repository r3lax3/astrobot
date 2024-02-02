import io

from typing import Optional, Union

from PIL import Image, ImageDraw, ImageFont

from src import config
from src.astro_engine.utils import get_moon_in_signs_interpretations
from src.enums import (
    Align,
    FileFormat,
    MoonPhase,
    ImageHighElementsPositions,
    ImageWideElementsPositions,
    ZodiacSign
)
from src.translations import ZODIAC_RU_TRANSLATION


# PATHS
FONT_PATH = "fonts/Comic Sans MS.ttf"

# COLOR
COLOR_WHITE = "#ffffff"

# FONT SIZES
DATE_FONT_SIZE = 68
TEXT_FONT_SIZE = 32
BLANK_MOON_FONT_SIZE = 40

# FONTS
DATE_FONT = ImageFont.truetype(FONT_PATH, DATE_FONT_SIZE)
TEXT_FONT = ImageFont.truetype(FONT_PATH, TEXT_FONT_SIZE)
BLANK_MOON_FONT = ImageFont.truetype(FONT_PATH, BLANK_MOON_FONT_SIZE)

# DATETIME FORMATS
DATETIME_FORMAT: str = config.get("database.datetime_format")
DATE_FORMAT: str = config.get("database.date_format")
TIME_FORMAT: str = config.get("database.time_format")

MOON_IN_SIGNS_INTERPRETATIONS = get_moon_in_signs_interpretations()


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
    blank_moon_caption: Optional[str] = None,
    image_element_position: Union[
        ImageWideElementsPositions,
        ImageHighElementsPositions
    ] = ImageHighElementsPositions
) -> bytes:
    # Open the background image
    background_image = Image.open(image_element_position.BACKGROUND_IMAGE_PATH.value)
    drawer = ImageDraw.Draw(background_image)

    if date is not None:
        drawer.text(
            calculate_adjust_for_centering(
                image_element_position.DATE_TEXT.value,
                date,
                DATE_FONT
            ),  # text size-adjusted position
            date,
            fill=COLOR_WHITE,
            font=DATE_FONT,
            align=Align.CENTER.value,
        )

    if start_sign is not None:
        first_sign_image = Image.open(
            f"images/moon_signs/{start_sign.value}.png"
        )
        first_sign_position = calculate_adjust_for_centering(
            image_element_position.START_MOON_SIGN_IMAGE.value,
            first_sign_image
        )

        background_image.paste(
            first_sign_image,
            first_sign_position,
            first_sign_image
        )

        first_sign_caption = f"Луна в {zodiac_sign_translate_to_russian(start_sign)}"

        drawer.text(
            calculate_adjust_for_centering(
                image_element_position.FIRST_MOON_SIGN_CAPTION.value,
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
            image_element_position.END_MOON_SIGN_IMAGE.value, end_sign_image
        )

        background_image.paste(end_sign_image, end_sign_position, end_sign_image)

        second_sign_caption = (
            f"c {change_time}  \nЛуна в {zodiac_sign_translate_to_russian(end_sign)}"
        )

        drawer.text(
            calculate_adjust_for_centering(
                image_element_position.SECOND_MOON_SIGN_CAPTION.value,
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
            image_element_position.MOON_PHASE.value,
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
                image_element_position.MOON_PHASE_CAPTION.value,
                moon_phase_caption,
                TEXT_FONT
            ),  # text size-adjusted position
            moon_phase_caption,
            fill=COLOR_WHITE,
            font=TEXT_FONT,
            align=Align.CENTER.value,
        )

    if blank_moon_caption is not None:
        drawer.text(
            calculate_adjust_for_centering(
                image_element_position.BLANK_MOON.value,
                blank_moon_caption,
                BLANK_MOON_FONT
            ),  # text size-adjusted position
            blank_moon_caption,
            fill=COLOR_WHITE,
            font=BLANK_MOON_FONT,
            align=Align.CENTER.value,
        )

    # Save or return the image
    byte_array = io.BytesIO()
    background_image.save(byte_array, format=FileFormat.JPEG.value)
    return byte_array.getvalue()
