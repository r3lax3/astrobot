import io

from PIL import Image, ImageDraw, ImageFont
from src import config


# Get the date format from the configuration
DATE_FORMAT: str = config.get(
    'database.date_format'
)
background_image_path = 'images/prediction_background.jpg'


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
    background_image = Image.open(background_image_path)
    text_drawer = ImageDraw.Draw(background_image)
    
    # Load the font for drawing the date
    font_path = "fonts/Comic Sans MS.ttf"
    font_size = 80
    font = ImageFont.truetype(font_path, font_size)
    

    # Draw the date on the image
    text_position = (404, 450)  # Подганял чётко под изображение методом тыка
    text_color = '#ffffff'
    text_drawer.text(
        text_position, 
        date, 
        fill=text_color, 
        font=font,
        align='center'
    )
    
    # Save the image to a BytesIO object
    byte_array = io.BytesIO()
    background_image.save(byte_array, format='JPEG')
    
    # Return the image data in bytes
    return byte_array.getvalue()

