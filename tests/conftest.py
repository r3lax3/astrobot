import pytest

from datetime import datetime
from unittest.mock import Mock

from src import config
from src.astro_engine.models import User as AstroUser
from src.astro_engine.models import Location

from tests.common import MOSKOW_LOCATION


DATETIME_FORMAT = "%d.%m.%Y %H:%M"
TEST_IMAGES_DIR = "tests/images/"

DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")
TIME_FORMAT = config.get("database.time_format")

HOURS_TIMEZONE_OFFSET = 3
MARIA_BIRTH_LOCATION = Location(longitude=37.817485, latitude=47.986848)
MARIA_CURRENT_LOCATION = Location(longitude=37.515761, latitude=55.799727)


@pytest.fixture
def user():
    user = Mock()

    user.timezone_offset = HOURS_TIMEZONE_OFFSET
    user.current_location = MARIA_CURRENT_LOCATION
    user.current_location_id = 1
    user.birth_location = MARIA_BIRTH_LOCATION
    user.birth_location_id = 2
    user.birth_datetime = "15.11.1979 05:15"

    return user


@pytest.fixture
def astro_user(user):
    return AstroUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=user.birth_location,
        current_location=user.current_location
    )
