from src.image_processing import generate_image_for_moon_signs
from src.enums import ZodiacSign, MoonPhase

# Define paths to the images for the astrological signs
START_SIGN_IMAGE = 'Gemini'  # Assuming the file name without extension

test_data_1 = {
    "date": "27.12.2023",
    "start_sign": ZodiacSign.CANCER,
    "moon_phase": MoonPhase.FULL_MOON,
    "moon_phase_caption": "15 Лунный день\nПОЛНАЯ ЛУНА\nc 15:34\n16 Лунный день"
}


image_bytes = generate_image_for_moon_signs(**test_data_1)

# Save the image to the root directory
output_image_path = 'astrology_image.jpeg'
with open(output_image_path, 'wb') as out_image:
    out_image.write(image_bytes)

print(f"Image saved to {output_image_path}")

# other_output_image_path = 'astrology_image2.jpeg'
# other_image_bs = generate_image_with_date_for_prediction(CHANGE_TIME)
# with open(other_output_image_path, 'wb') as out_image:
#     out_image.write(other_image_bs)
#
# print(f"Image saved to {other_output_image_path}")

