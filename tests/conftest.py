import pytest

from datetime import datetime
from unittest.mock import Mock

from src import config
from src.astro_engine.models import User as AstroUser
from src.astro_engine.models import Location
from src.enums import Gender


DATETIME_FORMAT = "%d.%m.%Y %H:%M"
TEST_IMAGES_DIR = "tests/images/"

DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")
TIME_FORMAT = config.get("database.time_format")

HOURS_TIMEZONE_OFFSET = 3
MARIA_BIRTH_LOCATION = Location(longitude=37.817485, latitude=47.986848)
MARIA_CURRENT_LOCATION = Location(longitude=37.515761, latitude=55.799727)

MARIA_BIRTH_LOCATION = Location(longitude=37.817485, latitude=47.986848)
MARIA_CURRENT_LOCATION = Location(longitude=37.515761, latitude=55.799727)
MARIA_BIRTH_DATE = "15.11.1979 05:15"



@pytest.fixture
def user():
    user = Mock()

    user.user_id = 824820503
    user.name = "Мария"

    user.birth_datetime = MARIA_BIRTH_DATE

    user.birth_location_id = 2
    user.birth_location = MARIA_BIRTH_LOCATION

    user.current_location_id = 1
    user.current_location = Location(longitude=135.103494, latitude=48.442037)  # напрямую заменил

    user.timezone_offset = HOURS_TIMEZONE_OFFSET

    user.subscription_end_date = "31.12.2026 12:00"
    user.gender = Gender.female.value

    return user


@pytest.fixture
def astro_user(user):
    return AstroUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=user.birth_location,
        current_location=user.current_location  # а тут как зависимость
    )
