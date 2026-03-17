import json
import os
import sys

CONFIG_FILE = "chess_bot_config.json"


def get_base_path():
    """Get base path for both script and frozen exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = get_base_path()

default_config = {
    "game_region": None,
    "light_cell_color": None,
    "dark_cell_color": None,
    "color_tolerance": 30,
    "move_delay": 500,
    "auto_revive": True,
    "templates_path": "templates/",
    "revive_button_pos": None,
}


def get_config_path():
    return os.path.join(BASE_PATH, CONFIG_FILE)


def get_templates_path():
    return os.path.join(BASE_PATH, "templates")


def save_config(config):
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            loaded = json.load(f)
            merged = default_config.copy()
            merged.update(loaded)
            return merged
    return default_config.copy()
