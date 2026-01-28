from datetime import datetime, timedelta

from src.astro_engine.moon.blank_moon import get_astro_events_from_period
from src.astro_engine.moon.sign import get_moon_sign_period, _get_moon_sign
from src.dicts import PLANET_ID_TO_NAME_RU
from src.enums import ZodiacSign

ZODIAC_SHORT = {
    ZodiacSign.ARIES: "Ari",
    ZodiacSign.TAURUS: "Tau",
    ZodiacSign.GEMINI: "Gem",
    ZodiacSign.CANCER: "Cnc",
    ZodiacSign.LEO: "Leo",
    ZodiacSign.VIRGO: "Vir",
    ZodiacSign.LIBRA: "Lib",
    ZodiacSign.SCORPIO: "Sco",
    ZodiacSign.SAGITTARIUS: "Sgr",
    ZodiacSign.CAPRICORN: "Cap",
    ZodiacSign.AQUARIUS: "Aqr",
    ZodiacSign.PISCES: "Psc",
}

ASPECT_NAMES = {
    0: "Conjunction",
    60: "Sextile",
    90: "Square",
    120: "Trine",
    180: "Opposition",
    240: "Trine",
    270: "Square",
    300: "Sextile",
}


def find_sign_changes(start: datetime, end: datetime, user) -> list[tuple[datetime, ZodiacSign]]:
    """Находит все моменты смены знака луны в периоде."""
    changes = []
    current_time = start
    current_sign = _get_moon_sign(current_time, user.current_location)
    
    step = timedelta(hours=1)
    
    while current_time <= end:
        new_sign = _get_moon_sign(current_time, user.current_location)
        if new_sign != current_sign:
            # Бинарный поиск точного момента
            left = current_time - step
            right = current_time
            while right - left > timedelta(minutes=1):
                mid = left + (right - left) / 2
                if _get_moon_sign(mid, user.current_location) == current_sign:
                    left = mid
                else:
                    right = mid
            changes.append((right, new_sign))
            current_sign = new_sign
        current_time += step
    
    return changes


def test_mono_astro_events_from_period(user, astro_user):
    # Задаём период напрямую
    start_date = datetime(2026, 1, 2, 0, 0)
    end_date = datetime(2026, 1, 31, 0, 0)
    
    timezone_offset = user.timezone_offset

    print(f"\n{'='*60}")
    print(f"Period: {start_date} - {end_date} (UTC)")
    print(f"Timezone offset: {timezone_offset}")
    print(f"{'='*60}\n")

    # Получаем все аспекты
    events = get_astro_events_from_period(start_date, end_date, astro_user)
    
    # Получаем все смены знаков
    sign_changes = find_sign_changes(start_date, end_date, astro_user)
    
    # Объединяем события и смены знаков в один список
    all_items = []
    
    for event in events:
        if event.peak:
            all_items.append(('event', event.peak, event))
    
    for change_time, new_sign in sign_changes:
        all_items.append(('sign_change', change_time, new_sign))
    
    # Сортируем по времени
    all_items.sort(key=lambda x: x[1])
    
    # Выводим
    for item_type, time, data in all_items:
        local_time = time + timedelta(hours=timezone_offset)
        
        if item_type == 'sign_change':
            sign_short = ZODIAC_SHORT.get(data, "???")
            print(f"{local_time.strftime('%d.%m.%Y %H:%M:%S')}  0°00'00\"{sign_short} <<<")
        else:
            event = data
            planet_name = PLANET_ID_TO_NAME_RU.get(event.second_planet, "?")
            aspect_name = ASPECT_NAMES.get(event.aspect, f"{event.aspect}°")
            print(f"{local_time.strftime('%d.%m.%Y %H:%M:%S')} {aspect_name} {planet_name}")
