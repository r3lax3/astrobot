from src.utils import load_yaml
from box import Box


messages = Box(
    load_yaml('i18n.yaml')['messages'] 
)

