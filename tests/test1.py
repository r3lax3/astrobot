from astropy.time import Time
from astropy.coordinates import get_body, solar_system_ephemeris
from astropy.utils.iers import conf
from enum import Enum
import numpy as np

# Это уменьшит задержку при первом вызове get_sun или get_moon, так как файл будет загружен при первом использовании
conf.auto_download = False

# Определение Enum для фаз Луны
class MoonPhase(Enum):
    NEW_MOON = "New Moon"
    WAXING_CRESCENT = "Waxing Crescent"
    FIRST_QUARTER = "First Quarter"
    WAXING_GIBBOUS = "Waxing Gibbous"
    FULL_MOON = "Full Moon"
    WANING_GIBBOUS = "Waning Gibbous"
    LAST_QUARTER = "Last Quarter"
    WANING_CRESCENT = "Waning Crescent"

# Диапазоны углов для каждой фазы Луны
MOON_PHASES_RANGES = {
    (0, 22.5): MoonPhase.NEW_MOON,
    (22.5, 67.5): MoonPhase.WAXING_CRESCENT,
    (67.5, 112.5): MoonPhase.FIRST_QUARTER,
    (112.5, 157.5): MoonPhase.WAXING_GIBBOUS,
    (157.5, 202.5): MoonPhase.FULL_MOON,
    (202.5, 247.5): MoonPhase.WANING_GIBBOUS,
    (247.5, 292.5): MoonPhase.LAST_QUARTER,
    (292.5, 337.5): MoonPhase.WANING_CRESCENT,
    (337.5, 360): MoonPhase.NEW_MOON,
}

# Функция для определения фазы Луны
def get_moon_phase(utcdatetime):
    # Установка времени для расчётов
    time = Time(utcdatetime)

    # Получение положения Солнца и Луны
    with solar_system_ephemeris.set('builtin'):
        sun = get_body('sun', time)
        moon = get_body('moon', time)
        print(f'{sun = }')
        print(f'{moon = }')

    # Вычисление угла элонгации Луны (угол между Солнцем и Луной)
    elongation = np.arccos(
        np.clip(
            np.dot(sun.cartesian.xyz.value, moon.cartesian.xyz.value) / (sun.distance.au * moon.distance.au),
            -1.0,
            1.0
        )
    )
    print(elongation)

    elongation_deg = elongation * 180.0 / np.pi  # Конвертация в градусы
    print(elongation_deg)

    # Определение фазы Луны на основе угла элонгации
    for (start, end), phase in MOON_PHASES_RANGES.items():
        if start <= elongation_deg < end:
            return phase

    # Если угол не попадает ни в один из диапазонов, считаем его новолунием
    return MoonPhase.NEW_MOON


# Тестирование функции с текущим временем
current_time = Time.now()
current_moon_phase = get_moon_phase(current_time.datetime)

print(current_moon_phase)
print(current_time.datetime)

