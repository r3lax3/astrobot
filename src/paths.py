"""Пути к файлам проекта.

Контент (толкования, сны, подборка дней) хранится в data/ как CSV/JSON:
таблицы правятся заказчицей вручную, без админки, поэтому файлы —
источник истины и версионируются вместе с кодом.
"""
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
DREAMS_INTERPRETATIONS_FILE = DATA_DIR / "dreams.csv"
INTERPRETATIONS_FILE = DATA_DIR / "interpretations.csv"
MOON_SIGNS_INTERPRETATIONS_FILE = DATA_DIR / "moon_signs_interpretations.csv"
DAY_SELECTION_FILE = DATA_DIR / "day_selection.json"

IMAGES_DIR = ROOT_DIR / "images"
FONTS_DIR = ROOT_DIR / "fonts"
