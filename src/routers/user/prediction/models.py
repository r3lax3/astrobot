from dataclasses import dataclass


@dataclass
class Interpretation:
    natal_planet: str
    transit_planet: str
    aspect: int
    general: str
    favorably: str
    unfavorably: str

