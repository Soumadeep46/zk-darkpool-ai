from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "config.yaml"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_config_value(*keys, default=None):
    config = load_config()

    for key in keys:
        if not isinstance(config, dict) or key not in config:
            return default

        config = config[key]

    return config