from datetime import datetime
import swisseph as swe
from src.astro_engine.utils import get_juliday


def test_juliday_comparison():
    """Сравниваем расчёт Julian Day."""
    
    ref_utc = datetime(2026, 1, 23, 13, 25, 30)
    
    # Твоя функция
    jd_yours = get_juliday(ref_utc)
    
    # Прямой вызов swisseph
    jd_direct = swe.julday(ref_utc.year, ref_utc.month, ref_utc.day,
                           ref_utc.hour + ref_utc.minute/60 + ref_utc.second/3600)
    
    print(f"Твой get_juliday:    {jd_yours}")
    print(f"Прямой swe.julday:   {jd_direct}")
    print(f"Разница:             {(jd_yours - jd_direct) * 24 * 60:.2f} минут")
    print()
    
    # Позиция луны с разными JD
    pos_yours = swe.calc_ut(jd_yours, swe.MOON)[0][0]
    pos_direct = swe.calc_ut(jd_direct, swe.MOON)[0][0]
    
    print(f"Позиция с твоим JD:    {pos_yours:.4f}°")
    print(f"Позиция с прямым JD:   {pos_direct:.4f}°")
