import datetime
import io

from PIL import Image, ImageDraw, ImageFont
from src import config


# Get the date format from the configuration
DATE_FORMAT: str = config.get(
    'database.date_format'
)


def generate_image_with_date_for_prediction(
    date_input=None
) -> bytes:
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
    background_image_path = 'images/фон для прогнозов.jpg'
    background_image = Image.open(background_image_path)
    text_drawer = ImageDraw.Draw(background_image)
    
    # Load the font for drawing the date
    font_path = "fonts/Comic Sans MS.ttf"
    font_size = 80
    font = ImageFont.truetype(font_path, font_size)
    
    # Check if a date is provided or use the current date
    if date_input is None:
        date_text = datetime.datetime.now().strftime(DATE_FORMAT)
    else:
        date_text = date_input

    # Draw the date on the image
    text_position = (370, 450)
    text_color = '#ffffff'
    text_drawer.text(
        text_position, 
        date_text, 
        fill=text_color, 
        font=font
    )
    
    # Save the image to a BytesIO object
    byte_array = io.BytesIO()
    background_image.save(byte_array, format='JPEG')
    
    # Return the image data in bytes
    return byte_array.getvalue()

