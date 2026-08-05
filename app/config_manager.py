import json
from pathlib import Path


class ConfigManager:

    def __init__(self):
        self.config = {}
        self.load()

    def load(self):

        settings_file = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "settings.json"
        )

        with open(settings_file, "r", encoding="utf-8") as file:
            self.config = json.load(file)

    def get(self, key, default=None):

        value = self.config

        for part in key.split("."):

            if not isinstance(value, dict):
                return default

            value = value.get(part)

            if value is None:
                return default

        return value