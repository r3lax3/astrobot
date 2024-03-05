import pytest

from unittest.mock import Mock
from datetime import datetime, timedelta

from src import config
from src.astro_engine.models import (
    Location,
    User as AstroUser
)
from src.astro_engine.predictions import get_astro_events_from_period
from src.dicts import PLANET_ID_TO_NAME_RU


TEST_IMAGES_DIR = "tests/images/"
DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")
TIME_FORMAT = config.get("database.time_format")

MOSKOW_LOCATION = Location(longitude=30.5238, latitude=50.45466)
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


def print_in_good_format_events(events):
    with open('tests/astrodata.txt', 'w') as f:
        for event in events:
            if event.peak_at is None:
                continue

            natal_planet_name = PLANET_ID_TO_NAME_RU.get(
                event.natal_planet,
                "Неизвестная планета"
            )
            transit_planet_name = PLANET_ID_TO_NAME_RU.get(
                event.transit_planet,
                "Неизвестная планета"
            )
            f.write(
                f"{event.peak_at.strftime('%d.%m.%Y %H:%M')} {natal_planet_name}, "
                f"{transit_planet_name}, {event.aspect}\n"
            )


def test_astro_events(user):
    astrouser = AstroUser(
        birth_datetime=datetime.strptime(user.birth_datetime, DATETIME_FORMAT),
        birth_location=user.birth_location,
        current_location=user.current_location
    )
    utcnow = datetime.utcnow()

    events = get_astro_events_from_period(
        utcnow - timedelta(days=15),
        utcnow + timedelta(days=15),
        astrouser
    )

    print_in_good_format_events(events)

