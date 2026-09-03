import json
from pathlib import Path

from app.config_manager import ConfigManager


class Settings:

    def __init__(self):

        root = Path(__file__).resolve().parents[1]

        with open(
            root / "config" / "settings.json",
            "r",
            encoding="utf-8",
        ) as f:

            self._settings = json.load(f)

    @property
    def application(self):
        return self._settings["application"]

    @property
    def author(self):
        return self._settings["author"]

    @property
    def tmdb_api_key(self):
        return ConfigManager().get(
            "tmdb.api_key",
            "",
        )


settings = Settings()
