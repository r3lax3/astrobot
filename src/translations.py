from src.enums import MoonPhase, ZodiacSign, PaymentMethod
from src.keyboards import bt
from src.payments import ProdamusPaymentService


ZODIAC_RU_TRANSLATION = {
    ZodiacSign.ARIES: "Овне",
    ZodiacSign.TAURUS: "Тельце",
    ZodiacSign.GEMINI: "Близнецах",
    ZodiacSign.CANCER: "Раке",
    ZodiacSign.LEO: "Льве",
    ZodiacSign.VIRGO: "Деве",
    ZodiacSign.LIBRA: "Весах",
    ZodiacSign.SCORPIO: "Скорпионе",
    ZodiacSign.SAGITTARIUS: "Стрельце",
    ZodiacSign.CAPRICORN: "Козероге",
    ZodiacSign.AQUARIUS: "Водолее",
    ZodiacSign.PISCES: "Рыбах",
}
MOON_PHASE_RU_TRANSLATIONS = {
    MoonPhase.NEW_MOON: "НОВОЛУНИЕ",
    MoonPhase.WAXING_CRESCENT: "Растущий\nполумесяц",
    MoonPhase.FIRST_QUARTER: "Первая\nчетверть",
    MoonPhase.WAXING_GIBBOUS: "Растущая луна",
    MoonPhase.FULL_MOON: "ПОЛНОЛУНИЕ",
    MoonPhase.WANING_GIBBOUS: "Убывающая луна",
    MoonPhase.LAST_QUARTER: "Последняя\nчетверть",
    MoonPhase.WANING_CRESCENT: "Убывающий\nполумесяц",
}

FROM_BT_TO_PAYMENT_METHOD = {
    # bt.yookassa: PaymentMethod.YOOKASSA,
    bt.prodamus: PaymentMethod.PRODAMUS
}

FROM_PAYMENT_METHOD_TO_PAYMENT_SERVICE = {
    # PaymentMethod.YOOKASSA: YookassaPaymentService,
    PaymentMethod.PRODAMUS: ProdamusPaymentService
}
