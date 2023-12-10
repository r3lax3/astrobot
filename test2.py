from PIL import Image, ImageDraw, ImageFont

# Get the date format from the configuration
BACKGROUND_IMAGE_PATH = 'images/purple_background.jpg'
COLOR_WHITE = '#ffffff'
FONT_PATH = "fonts/Comic Sans MS.ttf"
DATE_FONT_SIZE = 80
TEXT_FONT_SIZE = 32 

background_image = Image.open(BACKGROUND_IMAGE_PATH)
text_drawer = ImageDraw.Draw(background_image)

# Замените FONT_PATH и TEXT_FONT_SIZE на актуальные значения
text_font = ImageFont.truetype(FONT_PATH, DATE_FONT_SIZE)
date = "5.12.2023"
X, Y = 600, 500  # Центральная позиция для даты

_, _, w, h = text_drawer.textbbox((0, 0), date, font=text_font)

x = X - w / 2
y = Y - h / 2

# Для отладки нарисуйте рамку вокруг предполагаемой позиции текста
text_drawer.rectangle((x, y, x + w, y + h), outline="red")

text_drawer.text(
    (x, y),  # text size-adjusted position
    date, 
    fill="white",  # Замените на актуальное значение COLOR_WHITE
    font=text_font,
)
output_image_path = 'astrology_image.jpeg'
with open(output_image_path, 'wb') as f:
    background_image.save(f, format='JPEG')
print(f"Image saved to {output_image_path}")
