import json
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from app.local_configuration import (
    LocalConfiguration,
    LocalConfigurationError,
)


class SetupProfileError(RuntimeError):
    pass


class SetupProfileManager:

    VERSION = 1
    MAX_IMPORT_BYTES = 256 * 1024
    SUPPORTED_PROVIDERS = (
        "AIOStreams",
        "UsenetStreamer",
    )
    CONTAINER_PATTERN = re.compile(
        r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
    )
    RESOLUTION_PATTERN = re.compile(
        r"^(\d{3,5})x(\d{3,5})$"
    )

    def __init__(
        self,
        configuration=None,
        backup_root=None,
    ):

        self.configuration = (
            configuration or LocalConfiguration()
        )
        self.backup_root = Path(
            backup_root
            or self.configuration.project_root
            / "data"
            / "profile_backups"
        )
        self.state_path = (
            self.configuration.project_root
            / "data"
            / "profile"
            / "setup.json"
        )

    @staticmethod
    def _text(value, label, maximum=80):

        result = str(value or "").strip()

        if not result:
            raise SetupProfileError(
                f"{label} is required."
            )

        if len(result) > maximum or any(
            ord(character) < 32
            for character in result
        ):
            raise SetupProfileError(
                f"{label} is invalid."
            )

        return result

    @staticmethod
    def _number(value, label, minimum, maximum):

        try:
            result = float(value)
        except (TypeError, ValueError):
            raise SetupProfileError(
                f"{label} is invalid."
            )

        if not minimum <= result <= maximum:
            raise SetupProfileError(
                f"{label} is outside the supported range."
            )

        return int(result) if result.is_integer() else result

    @classmethod
    def _media(cls, document):

        if not isinstance(document, dict):
            raise SetupProfileError(
                "The media profile is invalid."
            )

        display = document.get("display")
        audio = document.get("audio")
        playback = document.get("playback")

        if not all(
            isinstance(section, dict)
            for section in (display, audio, playback)
        ):
            raise SetupProfileError(
                "The media profile is incomplete."
            )

        resolution = cls._text(
            display.get("resolution"),
            "Display resolution",
            maximum=20,
        )
        match = cls.RESOLUTION_PATTERN.fullmatch(
            resolution
        )

        if not match or any(
            not 320 <= int(dimension) <= 16384
            for dimension in match.groups()
        ):
            raise SetupProfileError(
                "Display resolution must look like 3840x2160."
            )

        restore = playback.get(
            "restore_desktop_after_playback"
        )
        hdr = display.get("hdr")

        if not isinstance(restore, bool) or not isinstance(
            hdr,
            bool,
        ):
            raise SetupProfileError(
                "The media profile contains invalid switches."
            )

        return {
            "display": {
                "name": cls._text(
                    display.get("name"),
                    "Display name",
                ),
                "desktop_refresh_rate": cls._number(
                    display.get("desktop_refresh_rate"),
                    "Desktop refresh rate",
                    20,
                    360,
                ),
                "movie_refresh_rate": cls._number(
                    display.get("movie_refresh_rate"),
                    "Movie refresh rate",
                    20,
                    120,
                ),
                "tv_refresh_rate": cls._number(
                    display.get("tv_refresh_rate"),
                    "TV refresh rate",
                    20,
                    120,
                ),
                "hdr": hdr,
                "resolution": resolution,
            },
            "audio": {
                "receiver": cls._text(
                    audio.get("receiver"),
                    "Audio receiver",
                ),
                # Version 1 exported profiles may contain the old
                # descriptive codec preference.  Normalise it because
                # playback audio must always follow the source content.
                "preferred_format": "Automatic",
            },
            "playback": {
                "player": cls._text(
                    playback.get("player"),
                    "Playback application",
                ),
                "restore_desktop_after_playback": restore,
            },
        }

    @classmethod
    def _services(cls, services):

        if not isinstance(services, list):
            raise SetupProfileError(
                "The service profile is invalid."
            )

        validated = []
        names = set()
        endpoints = set()

        for service in services:
            if not isinstance(service, dict):
                raise SetupProfileError(
                    "The service profile is invalid."
                )

            name = cls._text(
                service.get("name"),
                "Service name",
            )
            container = cls._text(
                service.get("container"),
                "Container name",
            )

            if not cls.CONTAINER_PATTERN.fullmatch(
                container
            ):
                raise SetupProfileError(
                    "A Docker container name is invalid."
                )

            try:
                port = int(service.get("port"))
            except (TypeError, ValueError):
                raise SetupProfileError(
                    "A service port is invalid."
                )

            if not 1 <= port <= 65535:
                raise SetupProfileError(
                    "A service port is invalid."
                )

            url = cls._text(
                service.get("url"),
                "Service URL",
                maximum=500,
            )
            parsed = urlsplit(url)

            try:
                parsed_port = parsed.port
            except ValueError:
                parsed_port = None

            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
                or parsed_port not in {None, port}
            ):
                raise SetupProfileError(
                    "A service URL is invalid or does not match its port."
                )

            name_key = name.casefold()
            endpoint_key = (container.casefold(), port)

            if name_key in names or endpoint_key in endpoints:
                raise SetupProfileError(
                    "The profile contains a duplicate service."
                )

            names.add(name_key)
            endpoints.add(endpoint_key)
            validated.append(
                {
                    "name": name,
                    "container": container,
                    "port": port,
                    "url": url,
                }
            )

        return validated

    @classmethod
    def _providers(cls, providers):

        if not isinstance(providers, list):
            raise SetupProfileError(
                "The playback-provider profile is invalid."
            )

        selected = []

        for provider in providers:
            name = str(provider or "").strip()

            if name not in cls.SUPPORTED_PROVIDERS:
                raise SetupProfileError(
                    f"The playback provider {name or 'unknown'} is not supported."
                )

            if name not in selected:
                selected.append(name)

        return selected

    @classmethod
    def validate(cls, profile):

        if not isinstance(profile, dict):
            raise SetupProfileError(
                "The Orion profile is invalid."
            )

        version = profile.get("version")

        if version != cls.VERSION:
            raise SetupProfileError(
                "This Orion profile version is not supported."
            )

        return {
            "version": cls.VERSION,
            "media": cls._media(profile.get("media")),
            "services": cls._services(
                profile.get("services")
            ),
            "providers": cls._providers(
                profile.get("providers")
            ),
        }

    def snapshot(self):

        try:
            media = self.configuration.read("media")
            services = self.configuration.read(
                "services"
            ).get("services")
            providers = self.configuration.read(
                "providers"
            ).get("providers")
        except LocalConfigurationError as error:
            raise SetupProfileError(str(error)) from error

        return self.validate(
            {
                "version": self.VERSION,
                "media": media,
                "services": services,
                "providers": providers,
            }
        )

    def completed(self):

        try:
            state = json.loads(
                self.state_path.read_text(
                    encoding="utf-8"
                )
            )
            return bool(state.get("completed"))
        except (OSError, ValueError, TypeError):
            return False

    def _backup(self):

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        path = self.backup_root / (
            "profile-"
            + datetime.now().strftime(
                "%Y%m%d-%H%M%S-%f"
            )
            + ".zip"
        )

        with zipfile.ZipFile(
            path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for kind in self.configuration.KINDS:
                source = self.configuration.ensure(kind)
                archive.write(
                    source,
                    arcname=f"profile/{source.name}",
                )

            if self.state_path.is_file():
                archive.write(
                    self.state_path,
                    arcname="profile/setup.json",
                )

        return path

    def save(self, profile, mark_complete=True):

        validated = self.validate(profile)
        backup = self._backup()
        originals = {}

        paths = {
            kind: self.configuration.local_path(kind)
            for kind in self.configuration.KINDS
        }

        for kind, path in paths.items():
            originals[kind] = (
                path.read_bytes()
                if path.is_file()
                else None
            )

        originals["state"] = (
            self.state_path.read_bytes()
            if self.state_path.is_file()
            else None
        )

        try:
            self.configuration.write(
                "media",
                validated["media"],
            )
            self.configuration.write(
                "services",
                {"services": validated["services"]},
            )
            self.configuration.write(
                "providers",
                {"providers": validated["providers"]},
            )

            if mark_complete:
                self.configuration._write_atomic(
                    self.state_path,
                    {
                        "version": self.VERSION,
                        "completed": True,
                    },
                )

            if self.snapshot() != validated:
                raise SetupProfileError(
                    "The saved profile could not be verified."
                )
        except Exception as error:
            for kind, path in paths.items():
                original = originals[kind]

                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    temporary = path.with_suffix(
                        path.suffix + ".rollback"
                    )
                    temporary.write_bytes(original)
                    os.replace(temporary, path)

            original_state = originals["state"]

            if original_state is None:
                self.state_path.unlink(missing_ok=True)
            else:
                temporary = self.state_path.with_suffix(
                    ".rollback"
                )
                temporary.write_bytes(original_state)
                os.replace(temporary, self.state_path)

            if isinstance(error, SetupProfileError):
                raise

            raise SetupProfileError(
                "Orion could not save the profile; the previous profile was restored."
            ) from error

        return backup

    def import_bytes(self, content):

        if not content or len(content) > self.MAX_IMPORT_BYTES:
            raise SetupProfileError(
                "Choose a valid Orion profile smaller than 256 KB."
            )

        try:
            profile = json.loads(
                content.decode("utf-8-sig")
            )
        except (UnicodeError, ValueError) as error:
            raise SetupProfileError(
                "The selected file is not a valid Orion profile."
            ) from error

        return self.save(profile)

    def export_text(self):

        return (
            json.dumps(
                self.snapshot(),
                indent=4,
                ensure_ascii=False,
            )
            + "\n"
        )
