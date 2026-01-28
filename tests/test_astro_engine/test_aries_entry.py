from datetime import datetime, timedelta
import swisseph as swe
from src.astro_engine.utils import get_juliday, get_planet_data
from src.astro_engine.models import Location
from src.enums import SwissEphPlanet


def test_aries_entry():
    """Проверяем вход в Овен — максимальная разница 87 минут."""
    
    loc = Location(longitude=135.103494, latitude=48.442037)
    target = 0.0  # 0° Овна
    
    # Референс: 23.01.2026 16:25:30 MSK = 13:25:30 UTC
    # Твой:     23.01.2026 17:52:30 MSK = 14:52:30 UTC
    
    ref_utc = datetime(2026, 1, 23, 13, 25, 30)
    my_utc = datetime(2026, 1, 23, 14, 52, 30)
    
    print("=== Позиция Луны в момент референса ===")
    jd = get_juliday(ref_utc)
    moon_pos = get_planet_data(jd, SwissEphPlanet.MOON, loc)[0][0]
    print(f"Время: {ref_utc} UTC / {ref_utc + timedelta(hours=3)} MSK")
    print(f"Позиция: {moon_pos:.6f}° (ожидаем 0°)")
    print()
    
    print("=== Позиция Луны в твой момент ===")
    jd2 = get_juliday(my_utc)
    moon_pos2 = get_planet_data(jd2, SwissEphPlanet.MOON, loc)[0][0]
    print(f"Время: {my_utc} UTC / {my_utc + timedelta(hours=3)} MSK")
    print(f"Позиция: {moon_pos2:.6f}° (ожидаем 0°)")
    print()
    
    print("=== Бинарный поиск точного входа в Овен ===")
    left = datetime(2026, 1, 23, 12, 0, 0)
    right = datetime(2026, 1, 23, 16, 0, 0)
    
    while (right - left).total_seconds() > 1:
        mid = left + (right - left) / 2
        jd = get_juliday(mid)
        pos = get_planet_data(jd, SwissEphPlanet.MOON, loc)[0][0]
        
        if pos < target or pos > 350:  # учитываем переход 359° -> 0°
            left = mid
        else:
            right = mid
    
    exact_utc = right
    jd = get_juliday(exact_utc)
    pos = get_planet_data(jd, SwissEphPlanet.MOON, loc)[0][0]
    
    print(f"Точный вход: {exact_utc} UTC / {exact_utc + timedelta(hours=3)} MSK")
    print(f"Позиция: {pos:.6f}°")
