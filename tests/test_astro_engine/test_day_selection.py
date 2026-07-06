from src.dicts import SWISSEPH_PLANET_TO_UNIVERSAL_PLANET
from src.database.models import User
from src.common import DAY_SELECTION_DATABASE
from src.astro_engine.predictions import get_astro_events_from_period_with_duplicates
from src.routers.user.prediction.text_formatting import (
    remove_duplicates_from_astro_events,
    format_astro_events_for_day_selection
)

from tests.utils import current_month_period


async def test_day_selection_pipeline(user: User, astro_user):
    """Полный пайплайн подбора дня: события за месяц -> фильтрация
    по выбранным аспектам -> форматирование в текст."""
    start, end = current_month_period()

    category = "Бизнес"
    action = "Начинать онлайн-проекты"
    selection = DAY_SELECTION_DATABASE[category][action]
    selected_aspects: list[dict] = selection["aspects"]
    favorably: bool = selection["favorably"]

    astro_events = await get_astro_events_from_period_with_duplicates(
        start=start,
        finish=end,
        user=astro_user,
    )
    assert astro_events, "За месяц должен найтись хотя бы один аспект"

    right_events = remove_duplicates_from_astro_events(
        astro_events,
        selected_aspects
    )
    assert right_events, "Для этой категории за месяц должны найтись события"

    # После фильтрации остаются только события из выбранных аспектов
    allowed = {
        (group["natal_planet"], group["transit_planet"], degree)
        for group in selected_aspects
        for degree in group["degrees"]
    }
    for event in right_events:
        key = (
            SWISSEPH_PLANET_TO_UNIVERSAL_PLANET[event.natal_planet],
            SWISSEPH_PLANET_TO_UNIVERSAL_PLANET[event.transit_planet],
            event.aspect,
        )
        assert key in allowed, f"Событие {key} не входит в выбранные аспекты"

    text = format_astro_events_for_day_selection(
        right_events,
        user.timezone_offset,
        favorably
    )
    assert text.strip(), "Форматирование должно вернуть непустой текст"
