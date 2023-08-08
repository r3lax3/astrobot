from geopy.geocoders import Nominatim


geolocator = Nominatim(user_agent="AstroBot")


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


