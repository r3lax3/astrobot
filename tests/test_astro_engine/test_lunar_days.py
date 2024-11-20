from datetime import timedelta

from src.astro_engine.moon.lunar_day import get_lunar_day
from src.utils import print_items_dict_as_table

from tests.utils import current_month_period
from tests.common import HOURS_TIMEZONE_OFFSET

LUNAR_DAYS_DATA_FILEPATH = "tests/data/lunar_days.txt"


def test_getting_lunar_day_transitions(user):
    start, end = current_month_period()

    start = start - timedelta(days=30)
    end = end - timedelta(days=30)

    with open(LUNAR_DAYS_DATA_FILEPATH, "w") as file:
        items = []
        tz_offset = timedelta(hours=HOURS_TIMEZONE_OFFSET)

        current_date = start
        while current_date <= end:

            lunar_day = get_lunar_day(
                current_date,
                user.current_location.longitude,
                user.current_location.latitude
            )

            day_start = (lunar_day.start + tz_offset).strftime('%d.%m %H:%M')
            day_end = (lunar_day.end + tz_offset).strftime('%d.%m %H:%M')

            day_number = f"{lunar_day.number:02}"

            items.append(
                {
                    "Номер": day_number,
                    "Начало": day_start,
                    "Конец": day_end
                }
            )

            current_date = lunar_day.end + timedelta(minutes=1)

        print_items_dict_as_table(items, file)
