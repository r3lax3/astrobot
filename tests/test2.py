from datetime import datetime, timedelta
from src.astro_engine.moon.sign import get_moon_sign_period, _get_moon_sign
from src.astro_engine.models import Location


def test_sign_period_debug(astro_user):
    timezone_offset = 3
    
    # Вариант 1: UTC полночь (как было)
    utc_midnight = datetime(2026, 1, 25, 0, 0)
    
    # Вариант 2: LOCAL полночь конвертированная в UTC
    local_midnight_as_utc = datetime(2026, 1, 24, 21, 0)  # 25 янв 00:00 LOCAL = 24 янв 21:00 UTC
    
    print("\n=== Вариант 1: UTC midnight (25 янв 00:00 UTC) ===")
    loc = astro_user.current_location
    sign = _get_moon_sign(utc_midnight, loc)
    print(f"Sign at this moment: {sign}")
    period = get_moon_sign_period(utc_midnight, astro_user)
    print(f"Sign period (UTC): {period.start} - {period.end}")
    
    print("\n=== Вариант 2: LOCAL midnight as UTC (24 янв 21:00 UTC) ===")
    sign = _get_moon_sign(local_midnight_as_utc, loc)
    print(f"Sign at this moment: {sign}")
    period = get_moon_sign_period(local_midnight_as_utc, astro_user)
    print(f"Sign period (UTC): {period.start} - {period.end}")
