from threading import ExceptHookArgs
import pytz

from datetime import datetime, timedelta

from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="AstroBot")


def get_timezone_offset(latitude, longitude) -> int:
    obj = TimezoneFinder()
    tz_name = obj.timezone_at(lat=latitude, lng=longitude)  # Получаем имя временной зоны
    if tz_name:
        timezone = pytz.timezone(tz_name)
        offset = timezone.utcoffset(datetime.utcnow())
        return int(offset.total_seconds() / 3600)  # Преобразуем в часы
    else:
        raise Exception(f"Can't get timezone name. {latitude = }, {longitude = }")


def convert_to_utc(dt: datetime, offset: int) -> datetime:
    return dt - timedelta(hours=offset)


def convert_from_utc(dt: datetime, offset: int) -> datetime:
    return dt + timedelta(hours=offset)


def is_int(string: str) -> bool:
    try:
        int(string)
        return True
    except (TypeError, ValueError):
        return False


def split_list(input_list: list, sublist_len: int = 2):
    """
    [1, 2, 3, 4] -> [[1, 2], [3, 4]]

    Типа дробит список на подсписки с определённой длинной
    Если список не делится нацело - остаток запихнёт в последний подсписок

    [1, 2, 3, 4, 5] -> [[1, 2], [3, 4], [5]]
    """
    return [
        input_list[i:i + sublist_len]
        for i in range(0, len(input_list), sublist_len)
    ]


def get_location_by_coords(longitude: float, latitude: float) -> str:
    location = geolocator.reverse((latitude, longitude), language='ru', exactly_one=True)

    if location and "address" in location.raw:
        address_info = location.raw["address"]

        # Вытягиваю наружу нужные мне данные из дикта
        city = address_info.get("city", "")
        town = address_info.get("town", "")
        village = address_info.get("village", "")
        region = address_info.get("region", "")
        district = address_info.get("district", "")
        state = address_info.get("state", "")
        country = address_info.get("country", "")

        if city:
            return f"{city}, {state}, {country}"
        elif region:
            return f"{region}, {state}, {country}"
        elif town:
            return f"{town}, {district}, {state}, {country}"
        elif village:
            return f"{village}, {district}, {state}, {country}"
        else:
            return country

    return "Ошибка. Напишите @mrAx3 насчет этого если увидите этот текст и не подтверждайте. Что-то сломалось."


