from skyfield.api import N, W, load, Topos
from datetime import datetime, timedelta
import math

def get_lunar_day(date: datetime) -> int:
    """
    Calculate the lunar day for a given date with precision up to minutes.

    Args:
    date (datetime): The date for which to calculate the lunar day.

    Returns:
    int: The lunar day
    """

    # Загрузить данные о положениях планет и Луны
    planets = load('de421.bsp')
    earth, moon = planets['earth'], planets['moon']

    # Использовать Topos для определения местоположения наблюдателя (пример: Гринвич, Великобритания)
    location = Topos('51.4769 N', '0.0005 W')

    # Получить положение Луны и Солнца относительно Земли
    ts = load.timescale()
    t = ts.utc(date.year, date.month, date.day, date.hour, date.minute, date.second)
    astrometric = (earth + location).at(t).observe(moon)
    alt, az, d = astrometric.apparent().altaz()

    # Рассчитать лунный день
    # Лунный день начинается при новолунии и длится примерно 29.53 дней
    # Используем формулу для расчета фазы Луны
    elongation = moon.elongation(t)
    phase = (elongation.degrees / 360) * 29.53
    lunar_day = math.ceil(phase)

    return lunar_day

# Пример использования функции
date = datetime(2023, 12, 11, 7, 9)
print(get_lunar_day(date))

