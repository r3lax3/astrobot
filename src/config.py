import tomllib


def get(key: str):
    with open('config.toml', 'rb') as f:
        target = tomllib.load(f)
        for part in key.split('.'):
            target = target[part]
        return target
