from aiogram import Router

from src import config, messages


r = Router()

date_format: str = config.get('database.date_format')
time_format: str = config.get('database.time_format')

zodiac_signs = [
    "Aries", 
    "Taurus",
    "Gemini", 
    "Cancer", 
    "Leo", 
    "Virgo",
    "Libra", 
    "Scorpio", 
    "Sagittarius", 
    "Capricorn", 
    "Aquarius", 
    "Pisces"
]

zodiac_translation = {
    "Aries": "Овне",
    "Taurus": "Тельце",
    "Gemini": "Близнецах",
    "Cancer": "Раке",
    "Leo": "Льве",
    "Virgo": "Деве",
    "Libra": "Весах",
    "Scorpio": "Скорпионе",
    "Sagittarius": "Стрельце",
    "Capricorn": "Козероге",
    "Aquarius": "Водолее",
    "Pisces": "Рыбах"
}
zodiac_bounds = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]

# Путь к вашему CSV файлу
moon_in_sign_csv_file_path = './moon_in_sign.csv'

# Словарь, который будет содержать данные
moon_in_signs_interpretation = {}

# Чтение CSV файла и заполнение словаря
with open(
    moon_in_sign_csv_file_path, 
    mode='r', 
    encoding='utf-8'
) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        sign = row['sign']
        moon_in_signs_interpretation[sign] = {
            'general': row['general'],
            'favorable': row['favorable'],
            'unfavorable': row['unfavorable']
        }


def translate_to_russian(english_name: str):
    return zodiac_translation.get(
        english_name, 
        "Неизвестный знак"
    )

def get_moon_sign(date: datetime):
    # Определение положения Луны
    moon = ephem.Moon(date)
    ecliptic_long = ephem.Ecliptic(moon).lon

    # Определение зодиакального созвездия для Луны
    ecliptic_long_deg = ecliptic_long * 180 / ephem.pi  # Перевод в градусы
    for i, bound in enumerate(zodiac_bounds):
        if ecliptic_long_deg < bound:
            return zodiac_signs[i - 1] if i > 0 else zodiac_signs[-1]

def find_moon_sign_change(
    date: datetime, 
    timezone_offset: int
) -> dict:
    date = date.replace(hour=0, minute=0)

    start_of_day = date + timedelta(hours=timezone_offset)
    end_of_day = start_of_day + timedelta(hours=23, minutes=58)
    
    start_sign = get_moon_sign(start_of_day)
    end_sign = get_moon_sign(end_of_day)
    
    result = {
        "start_sign": start_sign
    }
    
    if start_sign != end_sign:
        # Бинарный поиск времени смены знака
        left_time = start_of_day
        right_time = end_of_day

        while (right_time - left_time).total_seconds() > 60:  # пока разница во времени больше минуты
            middle_time = left_time + (right_time - left_time) / 2
            if get_moon_sign(middle_time) == start_sign:
                left_time = middle_time
            else:
                right_time = middle_time
        change_time = left_time

        result["change_time"] = change_time.strftime("%H:%M")
        result["end_sign"] = end_sign
    
    return result


def get_formatted_moon_sign_text(
    moon_signs: dict,
    type: str
) -> str:
    if type not in ['general', 'favorable', 'unfavorable']:
        raise Exception('Unexpected type of text for moon sign!')
    sign_changed_time: str = moon_signs.get('change_time', False)  # time string in format "%H:%m"

    if sign_changed_time:
        first_sign = moon_signs['start_sign']
        second_sign = moon_signs['end_sign']
        match type:
            case 'general':
                first_part = moon_in_signs_interpretation[first_sign]['general']
                second_part = moon_in_signs_interpretation[second_sign]['general']

            case 'favorable':
                first_part = messages.moon_sign_favourable.format(
                    text = moon_in_signs_interpretation[first_sign]['favorable']
                )
                second_part = messages.moon_sign_favourable.format(
                    text = moon_in_signs_interpretation[second_sign]['favorable']
                )

            case 'unfavorable':
                first_part = messages.moon_sign_unfavourable.format(
                    text = moon_in_signs_interpretation[first_sign]['unfavorable']
                )
                second_part = messages.moon_sign_unfavourable.format(
                    text = moon_in_signs_interpretation[second_sign]['unfavorable']
                )
            case _:
                first_part = "Ошибка."
                second_part = "Ошибка."
        
        # Преобразование строки в объект datetime
        time_obj = datetime.strptime(
            sign_changed_time,
            time_format
        )

        # Добавление одной минуты
        time_with_added_minute = time_obj + timedelta(minutes=1)
        time_str_with_added_minute = time_with_added_minute.strftime("%H:%M")

        text = messages.moon_sign_changed.format(
            first_time=sign_changed_time,
            second_time=time_str_with_added_minute,
            start_sign=translate_to_russian(first_sign),  # Из "Aries" в "Овна"
            end_sign=translate_to_russian(second_sign),  # Тут тоже
            first_part=first_part,
            second_part=second_part
        )

    else:
        match type:
            case 'general':
                sign = moon_signs['start_sign']
                interpretation_str = moon_in_signs_interpretation[sign]['general']
            case 'favorable':
                sign = moon_signs['start_sign']
                interpretation_str = messages.moon_sign_favourable.format(
                    text = moon_in_signs_interpretation[sign]['favorable']
                )

            case 'unfavorable':
                sign = moon_signs['start_sign']
                interpretation_str = messages.moon_sign_unfavourable.format(
                    text = moon_in_signs_interpretation[sign]['unfavorable']
                )

        text = messages.moon_sign_not_changed.format(
            start_sign=translate_to_russian(sign),
            text=interpretation_str
        )

    return text


