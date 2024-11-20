import pytest

import datetime as dt

from src.utils import print_items_dict_as_table
from src.dicts import PLANET_ID_TO_NAME_RU
from src.database.models import User
from src.common import DAY_SELECTION_DATABASE
from src.astro_engine.predictions import get_astro_events_from_period_with_duplicates
from src.routers.user.prediction.text_formatting import (
    remove_duplicates_from_astro_events,
    format_astro_events_for_day_selection
)

from tests.utils import current_month_period


@pytest.mark.asyncio
async def test_astro_events(user: User, astro_user):
    start, end = current_month_period()

    # start = start - dt.timedelta(days=30)
    # end = end - dt.timedelta(days=30)

    category = "Бизнес"
    action = "Начинать онлайн-проекты"
    selected_aspects: list[dict] = DAY_SELECTION_DATABASE[category][action]['aspects']
    favorably = DAY_SELECTION_DATABASE[category][action]['favorably']

    astro_events = await get_astro_events_from_period_with_duplicates(
        start=start,
        finish=end,
        user=astro_user,
    )
    print(len(astro_events))
    print_events(astro_events, "tests/data/day_selection_with_duplicates.txt")

    right_events = remove_duplicates_from_astro_events(
        astro_events,
        selected_aspects
    )
    print(len(right_events))
    print_events(right_events, "tests/data/day_selection_not_formatted.txt")

    text = format_astro_events_for_day_selection(
        right_events,
        user.timezone_offset,
        favorably
    )

    print(text, file=open("tests/data/day_selection_formatted.txt", "w"))


def print_events(events, file_path="tests/data/astrodata.txt"):
    items = [
        {
            "Транз": PLANET_ID_TO_NAME_RU[event.transit_planet],
            "Нат": PLANET_ID_TO_NAME_RU[event.natal_planet],
            "Асп.": event.aspect,
            "Время": (event.peak_at + dt.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")
        }
        for event in events
    ]
    sorted_items = sorted(items, key=lambda x: x["Время"])
    print_items_dict_as_table(
        sorted_items,
        open(file_path, "w")
    )
