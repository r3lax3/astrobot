import pytest

from datetime import datetime
from unittest.mock import Mock

from src import config
from src.astro_engine.models import User as AstroUser

from tests.common import MOSKOW_LOCATION


DATETIME_FORMAT = "%d.%m.%Y %H:%M"
TEST_IMAGES_DIR = "tests/images/"

DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")
TIME_FORMAT = config.get("database.time_format")

HOURS_TIMEZONE_OFFSET = 3


@pytest.fixture
def user():
    user = Mock()

    user.timezone_offset = HOURS_TIMEZONE_OFFSET
    user.current_location = MOSKOW_LOCATION
    user.current_location_id = 1
    user.birth_location = MOSKOW_LOCATION
    user.birth_location_id = 2
    user.birth_datetime = "19.10.2005 9:35"

    return user


@pytest.fixture
def astro_user(user):
    return AstroUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=user.birth_location,
        current_location=user.current_location
    )
