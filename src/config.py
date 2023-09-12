import tomllib

import tomli_w

from typing import Any


def get(key: str) -> int | str | dict[str, Any]:
    """
    Retrieve a value from the TOML configuration file based on the provided key.

    Args:
        key (str): The key to retrieve the value for, specified as a dot-separated path. 
                   For example, "bot.token" would retrieve the value of "token" inside the "bot" section.

    Returns:
        int | str | dict[str, Any]: The value associated with the provided key. 
                                    This can be an integer, string, or dictionary.

    Raises:
        KeyError: If the specified key is not found in the configuration.
    """
    with open('config.toml', 'rb') as f:
        target = tomllib.load(f)
        for part in key.split('.'):
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
    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)

    parts = key.split('.')
    target = config
    for part in parts[:-1]:
        target = target.setdefault(part, {})

    target[parts[-1]] = value

    with open('config.toml', 'wb') as f:
        tomli_w.dump(config, f)

