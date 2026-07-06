from datetime import datetime, timedelta

from src.astro_engine.moon.blank_moon import get_blank_moon_period


def test_blank_moon_period_matches_reference(user, astro_user):
    """Холостая луна 25.01.2026: эталонные значения из астрологического
    справочника — начало 00:36 (квадрат с Юпитером), конец 21:05 (вход в Тельца)."""
    timezone_offset = user.timezone_offset
    local_midnight = datetime(2026, 1, 25, 0, 0)
    utc_datetime = local_midnight - timedelta(hours=timezone_offset)

    blank_moon_period = get_blank_moon_period(
        utc_datetime, astro_user, timezone_offset
    )

    expected_start = datetime(2026, 1, 25, 0, 36)
    expected_end = datetime(2026, 1, 25, 21, 5)

    start_diff = abs(
        (blank_moon_period.start - expected_start).total_seconds() / 60
    )
    end_diff = abs(
        (blank_moon_period.end - expected_end).total_seconds() / 60
    )

    assert start_diff < 10, f"Start differs by {start_diff:.1f} minutes"
    assert end_diff < 10, f"End differs by {end_diff:.1f} minutes"
