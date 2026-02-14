import os
import yaml

_config = None


def load_config(path=None):
    global _config
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)
    return _config


def get_config():
    if _config is None:
        load_config()
    return _config
