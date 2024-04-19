from src.astro_engine.moon.blank_moon import get_astro_events_from_period
from src.dicts import PLANET_ID_TO_NAME_RU
from src.utils import print_items_dict_as_table

from tests.utils import current_month_period
from tests.common import DATETIME_FORMAT


def test_mono_astro_events_from_period(astro_user):
    start, end = current_month_period()

    # start = datetime.strptime('03.04.2024 06:20', DATETIME_FORMAT)
    # end = datetime.strptime('06.04.2024 11:27', DATETIME_FORMAT)

    events = get_astro_events_from_period(start, end, astro_user)

    # events = get_mono_astro_event_at_time(start, user)

    events = [
        {
            'Время': event.peak.strftime(DATETIME_FORMAT),
            'Планета': PLANET_ID_TO_NAME_RU[event.second_planet],
            'Аспект': event.aspect,
        }
        for event in events
    ]

    with open("tests/data/mono_astro_events.txt", "w") as file:

        file.write('Положение наблюдателя - Москва\n')
        file.write('Часовой пояс - Гринвич (+0)\n\n\n')

        print_items_dict_as_table(events, file)
