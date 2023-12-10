from src.image_processing import generate_image_with_signs, generate_image_with_date_for_prediction

# Define paths to the images for the astrological signs
START_SIGN_IMAGE = 'Gemini'  # Assuming the file name without extension

# Define date and times
DATE = "05.12.2023"
CHANGE_TIME = '12:15'

# Call the function to generate the image
image_bytes = generate_image_with_signs(
    date=DATE, 
    start_sign=START_SIGN_IMAGE, 
)

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

