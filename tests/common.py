from src.astro_engine.models import Location

from src import config

MOSKOW_LOCATION = Location(longitude=30.5238, latitude=50.45466)

DATETIME_FORMAT = "%d.%m.%Y %H:%M"
TEST_IMAGES_DIR = "tests/images/"

DATETIME_FORMAT = config.get("database.datetime_format")
DATE_FORMAT = config.get("database.date_format")
TIME_FORMAT = config.get("database.time_format")

HOURS_TIMEZONE_OFFSET = 3
