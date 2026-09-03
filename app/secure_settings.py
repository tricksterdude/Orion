import base64
import json
import os
import re
from pathlib import Path

from app.security.windows_dpapi import (
    WindowsDataProtector,
)


class SecureSettingsError(RuntimeError):
    pass


class SecureSettingsStore:

    TMDB_API_KEY = "tmdb.api_key"
    TMDB_KEY_PATTERN = re.compile(
        r"^[0-9a-f]{32}$",
        re.IGNORECASE,
    )
    ALLOWED_KEYS = {TMDB_API_KEY}

    def __init__(self, path=None, protector=None):

        self.path = Path(
            path
            or Path("data") / "secure_settings.json"
        )
        self.protector = (
            protector
            or WindowsDataProtector()
        )

    @classmethod
    def validate(cls, key, value):

        value = str(value or "").strip()

        if key not in cls.ALLOWED_KEYS:
            raise SecureSettingsError(
                "That private setting is not supported."
            )

        if (
            key == cls.TMDB_API_KEY
            and not cls.TMDB_KEY_PATTERN.fullmatch(value)
        ):
            raise SecureSettingsError(
                "Enter a valid 32-character TMDb API key."
            )

        return value

    def _read(self):

        if not self.path.is_file():
            return {}

        try:
            payload = json.loads(
                self.path.read_text(encoding="utf-8")
            )
            protected = base64.b64decode(
                payload["protected_data"],
                validate=True,
            )
            settings = json.loads(
                self.protector.unprotect(
                    protected
                ).decode("utf-8")
            )

            if not isinstance(settings, dict):
                raise ValueError("invalid settings")

            return {
                key: str(value)
                for key, value in settings.items()
                if key in self.ALLOWED_KEYS
            }
        except Exception as error:
            raise SecureSettingsError(
                "Orion could not unlock its private settings."
            ) from error

    def _write(self, settings):

        try:
            protected = self.protector.protect(
                json.dumps(
                    settings,
                    sort_keys=True,
                ).encode("utf-8")
            )
            payload = {
                "version": 1,
                "protected_data": base64.b64encode(
                    protected
                ).decode("ascii"),
            }

            self.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            temporary = self.path.with_suffix(
                self.path.suffix + ".tmp"
            )
            temporary.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.path)
        except SecureSettingsError:
            raise
        except Exception as error:
            raise SecureSettingsError(
                "Orion could not save its private settings."
            ) from error

    def get(self, key, default=None):

        if key not in self.ALLOWED_KEYS:
            return default

        return self._read().get(key, default)

    def set(self, key, value):

        settings = self._read()
        settings[key] = self.validate(key, value)
        self._write(settings)

    def delete(self, key):

        settings = self._read()

        if key not in settings:
            return False

        del settings[key]

        if settings:
            self._write(settings)
        elif self.path.exists():
            self.path.unlink()

        return True

    def configured(self, key):

        return bool(self.get(key))
