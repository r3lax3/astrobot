import tomllib

from typing import Any


def get(key: str) -> int | str | dict[str, Any]:
    with open('config.toml', 'rb') as f:
        target = tomllib.load(f)
        for part in key.split('.'):
            target = target[part]
        return target

