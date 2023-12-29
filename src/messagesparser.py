from box import Box

from src.utils import load_yaml

messages = Box(load_yaml("i18n.yaml")["messages"])
