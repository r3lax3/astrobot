import os
import pytest

from unittest.mock import Mock

from src import config
from src.image_processing.utils import get_image_with_astrodata
from src.astro_engine.models import Location


# Путь для сохранения тестовых изображений
TEST_IMAGES_DIR = "tests/images/"
DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")
TIME_FORMAT = config.get("database.time_format")

MOSKOW_LOCATION = Location(longitude=30.5238, latitude=50.45466)
HOURS_TIMEZONE_OFFSET = 3


@pytest.fixture
def user_mock():
    user = Mock()

    user.timezone_offset = HOURS_TIMEZONE_OFFSET
    user.current_location = MOSKOW_LOCATION
    user.current_location_id = 1
    user.birth_location = MOSKOW_LOCATION
    user.birth_location_id = 2
    user.birth_datetime = "19.10.2005 9:35"
    return user


@pytest.mark.asyncio
async def test_get_image_with_astrodata(user_mock):
    image_path = os.path.join(TEST_IMAGES_DIR, "test_image.jpg")

    image_bytes = await get_image_with_astrodata(user_mock)
    with open(image_path, 'wb') as image_file:
        image_file.write(image_bytes)

    assert os.path.exists(image_path)
