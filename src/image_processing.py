import io

from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from src import config
from src.enums import MoonPhase, PILPositions, Align, FileFormat


# Get the date format from the configuration
DATE_FORMAT: str = config.get('database.date_format')
BACKGROUND_IMAGE_PATH = 'images/purple_background.jpg'
DATE_TEXT_POSITION = (404, 450)  # Подганял чётко под изображение методом тыка
COLOR_WHITE = '#ffffff'
FONT_PATH = "fonts/Comic Sans MS.ttf"
DATE_FONT_SIZE = 80
TEXT_FONT_SIZE = 32 

zodiac_translation = {
    "Aries": "Овне",
    "Taurus": "Тельце",
    "Gemini": "Близнецах",
    "Cancer": "Раке",
    "Leo": "Льве",
    "Virgo": "Деве",
    "Libra": "Весах",
    "Scorpio": "Скорпионе",
    "Sagittarius": "Стрельце",
    "Capricorn": "Козероге",
    "Aquarius": "Водолее",
    "Pisces": "Рыбах"
}

date_font = ImageFont.truetype(FONT_PATH, DATE_FONT_SIZE)
text_font = ImageFont.truetype(FONT_PATH, TEXT_FONT_SIZE)


def zodiac_sign_translate_to_russian(english_name: str):
    return zodiac_translation.get(
        english_name, 
        "Неизвестный знак"
    )


def generate_image_with_date_for_prediction(date: str) -> bytes:
    """
    Generates an image with the given date or the current 
    date if none is provided.
    
    Parameters:
    - date_input (str, optional): 
        The date string to be added to the image. 
        If not provided, the current date will be used.
    
    Returns:
    - bytes: The image data in bytes.
    """
    # Open the background image
    background_image = Image.open(BACKGROUND_IMAGE_PATH)
    text_drawer = ImageDraw.Draw(background_image)
    
    # Draw the date on the image
    text_position = PILPositions.DATE_TEXT.value 
    text_color = COLOR_WHITE
    text_drawer.text(
        text_position, 
        date, 
        fill=text_color, 
        font=date_font,
        align=Align.CENTER.value
    )
    
    # Save the image to a BytesIO object
    byte_array = io.BytesIO()
    background_image.save(byte_array, format=FileFormat.JPEG.value)
    
    # Return the image data in bytes
    return byte_array.getvalue()


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


def generate_image_for_moon_signs(
    date: Optional[str] = None, 
    start_sign: Optional[str] = None,
    change_time: Optional[str] = None,
    end_sign: Optional[str] = None,
    moon_phase: Optional[MoonPhase] = None
) -> bytes:
    """
    Generates an image with astrological signs and transition time.

    Parameters:
    - date (str): The date string to be added to the image.
    - start_sign (str): File path for the starting astrological sign image.
    - change_time (str, optional): The time when the transition starts.
    - end_sign (str, optional): File path for the ending astrological sign image.
    - transition_time (str, optional): The transition time between signs.

    Returns:
    - bytes: The image data in bytes.
    """
    # Open the background image
    background_image = Image.open(BACKGROUND_IMAGE_PATH)
    drawer = ImageDraw.Draw(background_image)
    
    if date is not None: 
        drawer.text(
            calculate_adjust_for_centering(
                PILPositions.DATE_TEXT.value, 
                date, 
                date_font
            ),  # text size-adjusted position
            date, 
            fill=COLOR_WHITE, 
            font=date_font,
            align=Align.CENTER.value
        )

    if start_sign is not None:
        
        first_sign_image = Image.open(f'images/moon_signs/{start_sign}.png')
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
                text_font
            ),  # centered coordinates
            first_sign_caption,
            fill=COLOR_WHITE, 
            font=text_font,
            align=Align.CENTER.value
        )

    # If an end sign is given, load and paste 
    if change_time is not None and end_sign is not None:
        end_sign_image = Image.open(f'images/moon_signs/{end_sign}.png')
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
                text_font
            ),  # text size-adjusted position
            second_sign_caption,
            fill=COLOR_WHITE, 
            font=text_font,
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

    # Save or return the image
    byte_array = io.BytesIO()
    background_image.save(byte_array, format=FileFormat.JPEG.value)
    return byte_array.getvalue()

