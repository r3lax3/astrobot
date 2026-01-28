from datetime import datetime, timedelta
import swisseph as swe
from src.astro_engine.moon.blank_moon import (
    get_blank_moon_period,
    get_astro_events_from_period
)
from src.astro_engine.moon.sign import get_moon_sign_period, _get_moon_sign
from src.dicts import PLANET_ID_TO_NAME_RU


# def test_blank_moon(user, astro_user):
#     test_date = datetime(2026, 1, 25, 0, 0)
#     timezone_offset = user.timezone_offset
#
#     print(f"\n{'='*50}")
#
#     moon_sign_period = get_moon_sign_period(test_date, astro_user)
#     print(f"Moon sign period (UTC): {moon_sign_period.start} - {moon_sign_period.end}")
#
#     # Смотрим все аспекты в этом периоде
#     events = get_astro_events_from_period(
#         moon_sign_period.start,
#         moon_sign_period.end,
#         astro_user
#     )
#
#     print(f"\nAll moon aspects in this period (UTC):")
#     for event in events:
#         planet_name = PLANET_ID_TO_NAME_RU.get(event.second_planet, "?")
#         local_time = event.peak + timedelta(hours=timezone_offset)
#         print(f"  {event.peak} UTC | {local_time} LOCAL | {planet_name} {event.aspect}°")
#
#     if events:
#         latest = max(events, key=lambda e: e.peak)
#         print(f"\nLatest event (UTC): {latest.peak}")
#         print(f"Latest event (LOCAL): {latest.peak + timedelta(hours=timezone_offset)}")
#
#     print(f"\n{'='*50}")
#     print(f"Expected latest aspect (LOCAL): ~21:05 (so UTC should be ~18:05)")
#     print(f"{'='*50}")

# def test_jupiter_aspect():
#     # Наше время: 24.01.2026 22:53 UTC (01:53 LOCAL)
#     our_time = datetime(2026, 1, 24, 22, 53)
#
#     # Ожидаемое время: 25.01.2026 18:05 UTC (21:05 LOCAL)  
#     expected_time = datetime(2026, 1, 25, 18, 5)
#
#     for label, dt in [("Our time", our_time), ("Expected time", expected_time)]:
#         jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60)
#         moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
#         jupiter_pos = swe.calc_ut(jd, swe.JUPITER)[0][0]
#         diff = abs(moon_pos - jupiter_pos) % 360
#
#         print(f"\n{label}: {dt}")
#         print(f"  Moon: {moon_pos:.4f}°")
#         print(f"  Jupiter: {jupiter_pos:.4f}°")
#         print(f"  Diff: {diff:.4f}°")
#         print(f"  Diff from 90°: {abs(diff - 90):.4f}°")
#
#

def test_moon_signs():
    timezone_offset = 3
    
    # Разные точки 25 января LOCAL
    times = [
        ("00:00 LOCAL", datetime(2026, 1, 24, 21, 0)),   # 25 янв 00:00 LOCAL = 24 янв 21:00 UTC
        ("03:00 LOCAL", datetime(2026, 1, 25, 0, 0)),    # 25 янв 03:00 LOCAL = 25 янв 00:00 UTC
        ("12:00 LOCAL", datetime(2026, 1, 25, 9, 0)),    # 25 янв 12:00 LOCAL = 25 янв 09:00 UTC
        ("22:00 LOCAL", datetime(2026, 1, 25, 19, 0)),   # 25 янв 22:00 LOCAL = 25 янв 19:00 UTC
    ]
    
    for label, utc_time in times:
        from src.astro_engine.models import Location
        loc = Location(longitude=37.515761, latitude=55.799727)
        sign = _get_moon_sign(utc_time, loc)
        print(f"{label} (UTC {utc_time}): {sign}")


from datetime import datetime, timedelta

from src.astro_engine.moon.blank_moon import get_blank_moon_period
from src.astro_engine.moon.sign import get_moon_sign_period


def test_blank_moon_fixed(user, astro_user):
    # 25 января 2026, LOCAL полночь -> UTC
    timezone_offset = user.timezone_offset  # 3
    local_midnight = datetime(2026, 1, 25, 0, 0)
    utc_datetime = local_midnight - timedelta(hours=timezone_offset)
    
    print(f"\n{'='*60}")
    print(f"Testing blank moon for 25.01.2026 (LOCAL)")
    print(f"UTC datetime: {utc_datetime}")
    print(f"{'='*60}")
    
    # Получаем период знака
    moon_sign_period = get_moon_sign_period(utc_datetime, astro_user)
    print(f"\nMoon sign period (UTC):")
    print(f"  start: {moon_sign_period.start}")
    print(f"  end:   {moon_sign_period.end}")
    
    print(f"\nMoon sign period (LOCAL +{timezone_offset}):")
    print(f"  start: {moon_sign_period.start + timedelta(hours=timezone_offset)}")
    print(f"  end:   {moon_sign_period.end + timedelta(hours=timezone_offset)}")
    
    # Получаем период холостой луны
    blank_moon_period = get_blank_moon_period(utc_datetime, astro_user, timezone_offset)
    
    print(f"\nBlank moon period (LOCAL):")
    print(f"  start: {blank_moon_period.start}")
    print(f"  end:   {blank_moon_period.end}")
    
    print(f"\n{'='*60}")
    print(f"Expected (from reference):")
    print(f"  start: 25.01.2026 00:36 (Square Юпитер)")
    print(f"  end:   25.01.2026 21:05 (вход в Tau)")
    print(f"{'='*60}")
    
    # Проверки
    expected_start = datetime(2026, 1, 25, 0, 36)
    expected_end = datetime(2026, 1, 25, 21, 5)
    
    start_diff = abs((blank_moon_period.start - expected_start).total_seconds() / 60)
    end_diff = abs((blank_moon_period.end - expected_end).total_seconds() / 60)
    
    print(f"\nDifference from expected:")
    print(f"  start: {start_diff:.1f} minutes")
    print(f"  end:   {end_diff:.1f} minutes")
    
    # Допуск 5 минут
    assert start_diff < 10, f"Start differs by {start_diff:.1f} minutes"
    assert end_diff < 10, f"End differs by {end_diff:.1f} minutes"
