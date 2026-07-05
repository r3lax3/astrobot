from datetime import datetime, timedelta

from src.astro_engine.predictions import (
    get_astro_events_from_period_with_duplicates
)


async def test_astro_events(astro_user):
    utcnow = datetime.utcnow()

    events = await get_astro_events_from_period_with_duplicates(
        utcnow - timedelta(days=15),
        utcnow + timedelta(days=15),
        astro_user
    )

    assert events, "За месяц должен найтись хотя бы один астрособытийный аспект"

    for event in events:
        assert event.transit_planet is not None
        assert event.natal_planet is not None
        assert event.peak_at is not None
