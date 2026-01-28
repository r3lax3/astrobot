from datetime import datetime, timedelta
from src.astro_engine.moon.sign import _get_moon_sign, _calculate_moon_sign
from src.astro_engine.utils import get_juliday, calculate_planet_degrees_ut
from src.astro_engine.models import Location
from src.enums import SwissEphPlanet, ZodiacSign


def test_moon_sign_at_aries_entry():
    """Проверяем что возвращает _get_moon_sign около входа в Овен."""
    
    loc = Location(longitude=135.103494, latitude=48.442037)
    
    # Референс: 16:25:30 MSK = 13:25:30 UTC — говорит что это 0° Овна
    # Твой код: 17:52:30 MSK = 14:52:30 UTC — говорит что это 0° Овна
    
    times = [
        ("13:00 UTC", datetime(2026, 1, 23, 13, 0, 0)),
        ("13:25 UTC (референс)", datetime(2026, 1, 23, 13, 25, 30)),
        ("14:00 UTC", datetime(2026, 1, 23, 14, 0, 0)),
        ("14:52 UTC (твой)", datetime(2026, 1, 23, 14, 52, 30)),
        ("15:00 UTC", datetime(2026, 1, 23, 15, 0, 0)),
    ]
    
    for label, dt in times:
        jd = get_juliday(dt)
        degrees = calculate_planet_degrees_ut(jd, SwissEphPlanet.MOON, loc)
        sign = _get_moon_sign(dt, loc)
        calc_sign = _calculate_moon_sign(degrees)
        
        print(f"{label:25} -> {degrees:8.4f}° -> знак по _get_moon_sign: {sign.value:12} -> по _calculate: {calc_sign.value}")
