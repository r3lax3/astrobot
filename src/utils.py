import yaml
import pytz
import os
import ephem

from datetime import datetime, timedelta
from typing import Any

from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

from src.exceptions import PathDoesNotExistError


geolocator = Nominatim(user_agent="AstroBot")


def load_yaml(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


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
    location = geolocator.reverse(
        (
            latitude, 
            longitude
        ),
        language='ru',
        exactly_one=True
    )

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

    return "Ошибка. Напишите @mrAx3 насчет этого если увидите этот текст и ничего не трогайте. Что-то сломалось."


def path_validation(path: str) -> None:
    if not os.path.exists(path):
        raise PathDoesNotExistError(f"Путь не существует: {path}")


async def get_lunar_day(date: datetime, latitude: float, longitude: float):
    """
    Calculate the lunar day for a given date and location.
    
    Parameters:
    date (str): The date for which to calculate the lunar day, formatted as 'YYYY/MM/DD'.
    latitude (str): The latitude of the location, formatted as a string (e.g., '48.8566').
    longitude (str): The longitude of the location, formatted as a string (e.g., '2.3522').
    
    Returns:
    int: The lunar day number.
    """
    # Set up an observer at the given latitude and longitude
    observer = ephem.Observer()
    observer.lat, observer.lon = str(latitude), str(longitude)
    
    # Calculate the next and previous new moons relative to the given date
    next_new_moon = ephem.next_new_moon(date)
    last_new_moon = ephem.previous_new_moon(date)
    
    # Calculate the lunation as a fraction of the lunar month
    lunation = (observer.date - last_new_moon) / (next_new_moon - last_new_moon)
    
    # Calculate the lunar day, noting there are approximately 29.53 days in a lunar month
    lunar_day = lunation * 29.53
    
    # Return the lunar day as an integer, adding 1 since lunar days start at 1
    return int(lunar_day) + 1


def in_range(value: Any, start: Any, end: Any) -> bool:
    return start <= value < end

