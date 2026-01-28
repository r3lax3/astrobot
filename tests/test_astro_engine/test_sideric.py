from datetime import datetime, timedelta
import swisseph as swe


def test_sidereal_vs_tropical():
    """Сравниваем тропический и сидерический зодиак."""
    
    # Момент референса: 23.01.2026 13:25:30 UTC
    ref_utc = datetime(2026, 1, 23, 13, 25, 30)
    jd = swe.julday(ref_utc.year, ref_utc.month, ref_utc.day,
                    ref_utc.hour + ref_utc.minute/60 + ref_utc.second/3600)
    
    # Тропическая позиция (стандарт)
    tropical = swe.calc_ut(jd, swe.MOON)[0][0]
    print(f"Тропическая позиция: {tropical:.4f}°")
    print(f"  Знак: {int(tropical // 30)} (11 = Рыбы, 0 = Овен)")
    print()
    
    # Сидерическая позиция (Лахири — самая популярная аянамса)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sidereal = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    print(f"Сидерическая (Lahiri): {sidereal:.4f}°")
    print(f"  Знак: {int(sidereal // 30)}")
    print()
    
    # Аянамса
    ayanamsa = swe.get_ayanamsa_ut(jd)
    print(f"Аянамса (сдвиг): {ayanamsa:.4f}°")
    print()
    
    # Если референс в сидерике, то 0° Овна сидерического = ~24° Овна тропического
    print(f"0° Овна сидерического ≈ {ayanamsa:.1f}° тропического Овна")
