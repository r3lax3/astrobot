import pytest

from typing import List
from datetime import datetime

from src.astro_engine.moon.blank_moon import get_astro_events_from_period
from src.astro_engine.models import User, MonoAstroEvent
from src.dicts import PLANET_ID_TO_NAME_RU
from src.utils import print_items_dict_as_table

from .common import MOSKOW_LOCATION
from .utils import current_month_period

DATETIME_FORMAT = "%d.%m.%Y %H:%M"


@pytest.fixture
def user():
    return User(
        birth_datetime=datetime(1990, 1, 1),
        birth_location=MOSKOW_LOCATION,
        current_location=MOSKOW_LOCATION
    )


def format_astro_events(events: List[MonoAstroEvent]) -> str:
    lines = []

    for event in events:
        line = (
            f"{event.first_planet.name} {event.aspect} "
            f"{event.second_planet.name} at {event.peak.strftime('%Y-%m-%d %H:%M')}"
        )
        lines.append(line)

    return "\n".join(lines)


def save_astro_events_to_file(
    events: List[MonoAstroEvent],
    filename: str = "tests/test_data/mono_astro_events.txt"
):
    formatted_events = format_astro_events(events)

    with open(filename, "w") as file:
        file.write(formatted_events)

    print(f"Events saved to {filename}")


def test_mono_astro_events_from_period(user):
    start, end = current_month_period()

    # start = datetime.strptime('03.04.2024 06:20', DATETIME_FORMAT)
    # end = datetime.strptime('06.04.2024 11:27', DATETIME_FORMAT)

    events = get_astro_events_from_period(start, end, user)
    # events = get_mono_astro_event_at_time(start, user)

    events = [
        {
            'Время': event.peak.strftime(DATETIME_FORMAT),
            'Планета': PLANET_ID_TO_NAME_RU[event.second_planet],
            'Аспект': event.aspect,
        }
        for event in events
    ]

    with open("tests/mono_astro_events.txt", "w") as file:

        file.write('Положение наблюдателя - Москва\n')
        file.write('Часовой пояс - Гринвич (+0)\n\n\n')

        print_items_dict_as_table(events, file)
