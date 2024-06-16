from datetime import datetime, timedelta

from src.astro_engine.predictions import (
    get_astro_events_from_period_with_duplicates
)
from src.utils import print_items_dict_as_table
from src.dicts import PLANET_ID_TO_NAME_RU


def test_astro_events(astro_user):
    utcnow = datetime.utcnow()

    events = get_astro_events_from_period_with_duplicates(
        utcnow - timedelta(days=15),
        utcnow + timedelta(days=15),
        astro_user
    )

    items = [
        {
            "Транз": PLANET_ID_TO_NAME_RU[event.transit_planet],
            "Асп.": event.aspect,
            "Нат": PLANET_ID_TO_NAME_RU[event.natal_planet],
            "Время": (event.peak_at + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
        }
        for event in events
    ]
    sorted_items = sorted(items, key=lambda x: x["Время"])
    print_items_dict_as_table(
        sorted_items,
        open("tests/data/astrodata.txt", "w")
    )
