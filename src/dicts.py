from src.enums import Planets, SwissEphPlanet

MONTHS_TO_STR_MONTHS = {
    1: "1 месяц",
    2: "2 месяца",
    3: "3 месяца",
    6: "6 месяцев",
    12: "12 месяцев",
}

MONTHS_TO_RUB_PRICE = {
    1: 590,
    2: 1100,
    3: 1550,
    6: 2900,
    12: 5400
}

PLANET_ID_TO_NAME_RU = {
    0: "Солнце",
    1: "Луна",
    2: "Меркурий",
    3: "Венера",
    4: "Марс",
    5: "Юпитер",
    6: "Сатурн",
    7: "Уран",
    8: "Нептун",
    9: "Плутон",
}

SWISSEPH_PLANET_TO_UNIVERSAL_PLANET = {
    SwissEphPlanet.SUN: Planets.SUN,
    SwissEphPlanet.MOON: Planets.MOON,
    SwissEphPlanet.MERCURY: Planets.MERCURY,
    SwissEphPlanet.VENUS: Planets.VENUS,
    SwissEphPlanet.MARS: Planets.MARS,
    SwissEphPlanet.JUPITER: Planets.JUPITER,
    SwissEphPlanet.SATURN: Planets.SATURN,
    SwissEphPlanet.URANUS: Planets.URANUS,
    SwissEphPlanet.NEPTUNE: Planets.NEPTUNE,
    SwissEphPlanet.PLUTO: Planets.PLUTO,
}
