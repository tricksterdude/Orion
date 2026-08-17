import json
from pathlib import Path


class Settings:

    def __init__(self):

        root = Path(__file__).resolve().parents[2]

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
        return self._settings["tmdb"]["api_key"]


settings = Settings()