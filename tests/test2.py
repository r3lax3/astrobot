import ephem
import logging
 
from datetime import datetime, timedelta
from enum import Enum


class MoonPhase(Enum):
    NEW_MOON = "New Moon"
    WAXING_CRESCENT = "Waxing Crescent"
    FIRST_QUARTER = "First Quarter"
    WAXING_GIBBOUS = "Waxing Gibbous"
    FULL_MOON = "Full Moon"
    WANING_GIBBOUS = "Waning Gibbous"
    LAST_QUARTER = "Last Quarter"
    WANING_CRESCENT = "Waning Crescent"


MOON_PHASES_RANGES = {
    (0, 0.05): (MoonPhase.NEW_MOON),
    (0.05, 0.45): (MoonPhase.WAXING_CRESCENT, MoonPhase.WANING_CRESCENT),
    (0.45, 0.55): (MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER),
    (0.55, 0.95): (MoonPhase.WAXING_GIBBOUS, MoonPhase.WAXING_GIBBOUS),
    (0.95, 1): (MoonPhase.FULL_MOON),
}


# Define the observer's location
observer = ephem.Observer()


def get_moon_phase(observer: ephem.Observer) -> MoonPhase:
    moon = ephem.Moon()
    moon.compute(observer)
    current_phase = moon.moon_phase

    for (start, end), phase in MOON_PHASES_RANGES.items():
        if not (start <= current_phase <= end):
            continue
        
        if 0.05 < current_phase < 0.95:
            # Вычисляем процент освещенности за 6 часов до текущего момента
            observer.date = observer.date.datetime() - timedelta(hours=6)
            moon.compute(observer)
            past_phase = moon.moon_phase

            # Определяем, растущая или убывающая фаза
            is_waxing = current_phase > past_phase

            return phase[0] if is_waxing else phase[1]
    else:
        logging.error(
            f'get_moon_phase Нет подходящего диапазона для текущего лунного освещения - {current_phase}'
        )
        return MoonPhase.NEW_MOON


observer.lat = '50.4440'
observer.long = '30.5395'
observer.date = datetime.utcnow()
 
# Print the phase of the moon
print(get_moon_phase(observer))

