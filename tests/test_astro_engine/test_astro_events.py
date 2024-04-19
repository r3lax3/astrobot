from typing import List
from datetime import datetime, timedelta

from src.astro_engine.moon.blank_moon import get_astro_events_from_period
from src.astro_engine.models import MonoAstroEvent

from tests.utils import save_events_to_data


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
    filename: str = "tests/data/mono_astro_events.txt"
):
    formatted_events = format_astro_events(events)

    with open(filename, "w") as file:
        file.write(formatted_events)

    print(f"Events saved to {filename}")


def test_astro_events(astro_user):
    utcnow = datetime.utcnow()

    events = get_astro_events_from_period(
        utcnow - timedelta(days=15),
        utcnow + timedelta(days=15),
        astro_user
    )

    save_events_to_data(events)
