from datetime import timedelta

from src.astro_engine.moon.lunar_day import get_lunar_day

from tests.utils import current_month_period


def test_lunar_days_are_valid_and_contiguous(user):
    """Лунные дни за месяц: номера корректны, периоды идут встык
    и нумерация растёт на 1 (со сбросом на новолунии)."""
    start, end = current_month_period()

    previous = None
    count = 0
    current_date = start

    while current_date <= end:
        lunar_day = get_lunar_day(
            current_date,
            user.current_location.longitude,
            user.current_location.latitude
        )

        assert 1 <= lunar_day.number <= 30
        assert lunar_day.start < lunar_day.end

        if previous is not None:
            assert lunar_day.number in (previous.number + 1, 1), (
                f"После {previous.number}-го дня идёт {lunar_day.number}-й"
            )
            gap = abs((lunar_day.start - previous.end).total_seconds())
            assert gap <= 120, (
                f"Разрыв {gap:.0f} с между днями "
                f"{previous.number} и {lunar_day.number}"
            )

        previous = lunar_day
        count += 1
        current_date = lunar_day.end + timedelta(minutes=1)

    assert count >= 28, f"За месяц найдено только {count} лунных дней"
