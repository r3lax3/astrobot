from datetime import datetime, timedelta
from src.astro_engine.utils import get_juliday, get_planet_data
from src.astro_engine.models import Location
from src.enums import SwissEphPlanet


# def test_moon_position_check():
#     # Момент из референса: 2.01.2026 16:08:48 UTC — луна входит в Рак (0°00'00" Cnc)
#     # У тебя: 02.01.2026 15:47:48 — разница ~21 минута
#
#     test_location = Location(longitude=135.103494, latitude=48.442037)
#
#     # Проверим позицию луны в момент из референса
#     ref_time = datetime(2026, 1, 2, 16, 8, 48)  # UTC
#     jd = get_juliday(ref_time)
#
#     moon_data = get_planet_data(jd, SwissEphPlanet.MOON, test_location)
#     moon_pos = moon_data[0][0]
#
#     print(f"Референс время (UTC): {ref_time}")
#     print(f"Позиция Луны: {moon_pos:.6f}°")
#     print(f"Знак: {int(moon_pos // 30)} (3 = Рак)")
#     print(f"Градус в знаке: {moon_pos % 30:.6f}°")
#     print()
#
#     # Проверим в твоё время
#     my_time = datetime(2026, 1, 2, 15, 47, 48)  # UTC  
#     jd2 = get_juliday(my_time)
#
#     moon_data2 = get_planet_data(jd2, SwissEphPlanet.MOON, test_location)
#     moon_pos2 = moon_data2[0][0]
#
#     print(f"Твоё время (UTC): {my_time}")
#     print(f"Позиция Луны: {moon_pos2:.6f}°")
#     print(f"Знак: {int(moon_pos2 // 30)} (3 = Рак)")
#     print(f"Градус в знаке: {moon_pos2 % 30:.6f}°")
#     print()
#
#     # Проверим без топоцентрической коррекции
#     moon_data3 = get_planet_data(jd, SwissEphPlanet.MOON, None)
#     moon_pos3 = moon_data3[0][0]
#
#     print(f"Референс время БЕЗ топоцентрики: {moon_pos3:.6f}°")
#     print(f"Разница с топоцентрикой: {(moon_pos - moon_pos3) * 60:.2f} угловых минут")


def test_find_exact_sign_entry():
    test_location = Location(longitude=135.103494, latitude=48.442037)
    
    # Бинарный поиск момента когда луна = 90.0° (вход в Рак)
    left = datetime(2026, 1, 2, 12, 0, 0)
    right = datetime(2026, 1, 2, 17, 0, 0)
    target = 90.0
    
    while (right - left).total_seconds() > 1:
        mid = left + (right - left) / 2
        jd = get_juliday(mid)
        moon_pos = get_planet_data(jd, SwissEphPlanet.MOON, test_location)[0][0]
        
        if moon_pos < target:
            left = mid
        else:
            right = mid
    
    exact_time_utc = left + (right - left) / 2
    jd = get_juliday(exact_time_utc)
    moon_pos = get_planet_data(jd, SwissEphPlanet.MOON, test_location)[0][0]
    
    print(f"Точный вход в Рак (90°):")
    print(f"  UTC:    {exact_time_utc.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"  UTC+3:  {(exact_time_utc + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"  Позиция: {moon_pos:.6f}°")
    print()
    print(f"Референс (MSK): 02.01.2026 16:08:48")
    print(f"Твой (MSK):     02.01.2026 {(datetime(2026,1,2,15,47,48) + timedelta(hours=3)).strftime('%H:%M:%S')}")
