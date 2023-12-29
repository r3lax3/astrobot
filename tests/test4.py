import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Tuple

import swisseph as swe


@dataclass
class Location:
    latitude: float
    longitude: float


class ZodiacSign(Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"

class SwissEphPlanet(Enum):
    SUN = 0
    MOON = 1
    MERCURY = 2
    VENUS = 3
    MARS = 4
    JUPITER = 5
    SATURN = 6
    URANUS = 7
    NEPTUNE = 8
    PLUTO = 9

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
    ZodiacSign.PISCES
]
ZODIAC_BOUNDS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
READABLE_DATETIME_FORMAT = '%d.%m.%Y, %H:%M'


def get_juliday(utc_date: datetime) -> float:
    """Calculates julian day from the utc time."""
    utc_time = utc_date.hour + utc_date.minute / 60
    julian_day = float(swe.julday(utc_date.year, utc_date.month, utc_date.day, utc_time))
    return julian_day

def calculate_moon_degrees_ut(juliday: float, location: Location):
    # Установка топографических координат наблюдателя
    swe.set_topo(location.longitude, location.latitude, 0)

    flag = swe.FLG_SWIEPH + swe.FLG_SPEED + swe.FLG_TOPOCTR
    return swe.calc(juliday, SwissEphPlanet.MOON.value, flag)[0][0]

def calculate_moon_sign(moon_degrees: float) -> ZodiacSign:
    for i, bound in enumerate(ZODIAC_BOUNDS):
        if moon_degrees < bound:
            return ZODIAC_SIGNS[i]
    else:
        return ZODIAC_SIGNS[-1]

def get_moon_sign(date: datetime, location: Location) -> ZodiacSign:
    juliday = get_juliday(date)
    moon_degree = calculate_moon_degrees_ut(juliday, location)
    return calculate_moon_sign(moon_degree)



def moon_signs_summary(
    start_date: datetime,
    end_date: datetime,
    location: Location
) -> List[Tuple[datetime, ZodiacSign]]:
    current_date = start_date
    summary = []
    previous_sign = get_moon_sign(current_date, location)
    while current_date <= end_date:
        current_sign = get_moon_sign(current_date, location)
        if current_sign != previous_sign:
            summary.append((current_date, current_sign))
            previous_sign = current_sign
        current_date += timedelta(minutes=1)
    return summary


example_location = Location(latitude=55.7558, longitude=37.6173)

# Пример использования
now = datetime.utcnow()
start_date = now - timedelta(days=30)
end_date = now + timedelta(days=30)

start_time = time.time()

transitions = moon_signs_summary(start_date, end_date, example_location)

end_time = time.time()
execution_time = end_time - start_time
print(f"Время выполнения: {execution_time:.3f} секунд")
for date, sign in transitions:
    date += timedelta(hours=3)
    print(f"{date.strftime(READABLE_DATETIME_FORMAT)} - {sign.value}")

