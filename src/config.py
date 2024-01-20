import tomllib
from typing import Any

import tomli_w


def get(key: str) -> Any:
    """
    Retrieve a value from TOML config based on the provided key.

    Args:
        key (str): The key to retrieve, as a dot-separated path. E.g.,
                   "bot.token" would get "token" inside the "bot" section.

    Returns:
        int | str | Dict[str, Any] | List[int | str | float]:
            The value for the provided key. Can be an integer, string,
            dictionary, or a list of integers, strings, and floats.

    Raises:
        KeyError: If the key is not found in the configuration.
    """
    with open("config.toml", "rb") as f:
        target = tomllib.load(f)
        for part in key.split("."):
            target = target[part]
        return target


def set(key: str, value: Any) -> None:
    """
    Set a value in the TOML configuration file based on the provided key.

    Args:
        key (str): The key to set the value for, specified as a dot-separated path.
                   For example, "bot.token" would set the value of "token" inside the "bot" section.
        value (Any): The value to set for the specified key. This can be an integer, string, or dictionary.

    Raises:
        KeyError: If any part of the key path (except for the last part) is not found in the configuration
                  and cannot be created.
    """
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    parts = key.split(".")
    target = config
    for part in parts[:-1]:
        target = target.setdefault(part, {})

    target[parts[-1]] = value

    with open("config.toml", "wb") as f:
        tomli_w.dump(config, f)

