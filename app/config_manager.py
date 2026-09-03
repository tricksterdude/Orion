import json
from pathlib import Path

from app.secure_settings import (
    SecureSettingsError,
    SecureSettingsStore,
)


class ConfigManager:

    def __init__(
        self,
        settings_file=None,
        secure_settings=None,
    ):
        self.config = {}
        self.settings_file = Path(
            settings_file
            or Path(__file__).resolve().parent.parent
            / "config"
            / "settings.json"
        )
        self.secure_settings = (
            secure_settings
            or SecureSettingsStore()
        )
        self.load()

    def load(self):

        with open(
            self.settings_file,
            "r",
            encoding="utf-8",
        ) as file:
            self.config = json.load(file)

        legacy_key = (
            self.config.get("tmdb", {}).get(
                "api_key"
            )
        )

        try:
            private_key = self.secure_settings.get(
                SecureSettingsStore.TMDB_API_KEY
            )

            if not private_key and legacy_key:
                self.secure_settings.set(
                    SecureSettingsStore.TMDB_API_KEY,
                    legacy_key,
                )
                private_key = legacy_key
        except SecureSettingsError:
            private_key = legacy_key

        if private_key:
            self.config.setdefault("tmdb", {})[
                "api_key"
            ] = private_key

    def get(self, key, default=None):

        value = self.config

        for part in key.split("."):

            if not isinstance(value, dict):
                return default

            value = value.get(part)

            if value is None:
                return default

        return value
