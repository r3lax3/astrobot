from datetime import datetime, timedelta

from src.dicts import PLANET_ID_TO_NAME_RU


def current_month_period():
    today = datetime.today()
    start_of_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        end_of_month = datetime(
            today.year + 1,
            1,
            1
        ) - timedelta(days=1)
    else:
        end_of_month = datetime(
            today.year,
            today.month + 1,
            1
        ) - timedelta(days=1)
    return start_of_month, end_of_month


def save_events_to_data(events):
    with open('tests/data/astrodata.txt', 'w') as f:
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
