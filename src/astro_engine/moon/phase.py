import logging
from datetime import date, datetime, timedelta

import ephem

from src import config
from src.enums import MoonPhase, ZodiacSign


# Константы
SECONDS_IN_DAY = 24 * 60 * 60
ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
ZODIAC_SIGNS = [
    ZodiacSign.ARIES,
    ZodiacSign.TAURUS,
    ZodiacSign.GEMINI,
    ZodiacSign.CANCER,
    ZodiacSign.LEO,
    ZodiacSign.VIRGO,
    ZodiacSign.LIBRA,
    ZodiacSign.SCORPIO,
    ZodiacSign.SAGITTARIUS,
    ZodiacSign.CAPRICORN,
    ZodiacSign.AQUARIUS,
    ZodiacSign.PISCES,
]

MOON_PHASES_RANGES = {
    (0, 0.05): MoonPhase.NEW_MOON,
    (0.05, 0.45): (MoonPhase.WAXING_CRESCENT, MoonPhase.WANING_CRESCENT),
    (0.45, 0.55): (MoonPhase.FIRST_QUARTER, MoonPhase.LAST_QUARTER),
    (0.55, 0.99): (MoonPhase.WAXING_GIBBOUS, MoonPhase.WANING_GIBBOUS),
    (0.99, 1): MoonPhase.FULL_MOON,
}
ISO_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT: str = config.get("database.time_format")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

LOGGER = logging.getLogger(__name__)


def get_moon_phase(date: date, longitude: float, latitude: float) -> MoonPhase:
    """
    Вычисляет фазу Луны для заданной даты и координат.
    """
    observer = ephem.Observer()
    observer.date = datetime(date.year, date.month, date.day)
    observer.lon = str(longitude)
    observer.lat = str(latitude)

    moon = ephem.Moon(observer)
    current_phase = moon.moon_phase

    for (start, end), phase in MOON_PHASES_RANGES.items():
        if start <= current_phase <= end:
            if isinstance(phase, tuple):
                # Определение растущей или убывающей фазы Луны
                observer.date = observer.date.datetime() - timedelta(
                    hours=6
                )  # Смещение на 6 часов назад
                moon.compute(observer)
                is_waxing = current_phase > moon.moon_phase
                return phase[0] if is_waxing else phase[1]
            else:
                return phase
    logging.error(
        f"get_moon_phase: No suitable range for current phase - {current_phase}"
    )
    return MoonPhase.NEW_MOON
