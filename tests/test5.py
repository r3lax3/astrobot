from datetime import datetime, timedelta

import ephem


# Функция для определения знака Зодиака Луны на определенную дату
def get_moon_sign(date):
    observer = ephem.Observer()
    observer.lat, observer.lon = '55.7558', '37.6173'  # Координаты Москвы
    observer.date = date
    moon = ephem.Moon(observer)
    sun = ephem.Sun(observer)
    moon.compute(observer)
    sun.compute(observer)
    # Вычисляем положение Луны относительно Солнца в эклиптических координатах
    ecl_lon = ephem.Ecliptic(moon).lon - ephem.Ecliptic(sun).lon
    ecl_lon = ecl_lon % ephem.degrees('360')
    ecl_lon = float(ecl_lon)
    
    # Определение знака Зодиака на основе эклиптической долготы
    sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 
                  'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_degrees = [30 * i for i in range(12)]  # Градусы для каждого знака
    for i in range(12):
        if ecl_lon < sign_degrees[i]:
            return sign_names[i-1]
    return sign_names[-1]

# Проверяем дату 16 ноября 2023 года
test_date = datetime(2023, 11, 16, 11, 16) - timedelta(hours=3) # часовой пояс
print(get_moon_sign(test_date))

