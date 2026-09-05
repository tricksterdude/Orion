import json
import os
import threading
from pathlib import Path


class LocalConfigurationError(RuntimeError):
    pass


class LocalConfiguration:

    KINDS = {
        "services": {
            "legacy": Path("config") / "services.json",
            "local": Path("data") / "profile" / "services.json",
            "default": {"services": []},
        },
        "providers": {
            "legacy": Path("config") / "providers.json",
            "local": Path("data") / "profile" / "providers.json",
            "default": {"providers": []},
        },
        "media": {
            "legacy": Path("data") / "media_profile.json",
            "local": Path("data") / "profile" / "media.json",
            "default": {
                "display": {
                    "name": "Primary display",
                    "desktop_refresh_rate": 60,
                    "hdr": False,
                    "resolution": "1920x1080",
                },
                "audio": {
                    "receiver": "Not configured",
                    "preferred_format": "Automatic",
                    "receiver_adapter": "none",
                    "receiver_host": "",
                },
                "playback": {
                    "player": "Stremio",
                    "restore_desktop_after_playback": True,
                },
            },
        },
    }

    def __init__(self, project_root=None):

        self.project_root = Path(
            project_root
            or Path(__file__).resolve().parents[1]
        )
        self._lock = threading.RLock()

    def _definition(self, kind):

        if kind not in self.KINDS:
            raise LocalConfigurationError(
                "That Orion configuration is not supported."
            )

        return self.KINDS[kind]

    def legacy_path(self, kind):

        return self.project_root / self._definition(kind)[
            "legacy"
        ]

    def local_path(self, kind):

        return self.project_root / self._definition(kind)[
            "local"
        ]

    @staticmethod
    def _serialise(document):

        return (
            json.dumps(
                document,
                indent=4,
                ensure_ascii=False,
            )
            + "\n"
        )

    @staticmethod
    def _write_atomic(path, document):

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(
            path.suffix + ".tmp"
        )
        temporary.write_text(
            LocalConfiguration._serialise(document),
            encoding="utf-8",
        )
        os.replace(temporary, path)

    def ensure(self, kind):

        destination = self.local_path(kind)

        with self._lock:
            if destination.is_file():
                return destination

            source = self.legacy_path(kind)

            try:
                if source.is_file():
                    document = json.loads(
                        source.read_text(encoding="utf-8")
                    )
                else:
                    document = json.loads(
                        json.dumps(
                            self._definition(kind)["default"]
                        )
                    )

                self._write_atomic(destination, document)
            except (OSError, ValueError, TypeError) as error:
                raise LocalConfigurationError(
                    f"Orion could not prepare its local {kind} configuration."
                ) from error

        return destination

    def read(self, kind):

        path = self.ensure(kind)

        try:
            document = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError, TypeError) as error:
            raise LocalConfigurationError(
                f"Orion could not read its local {kind} configuration."
            ) from error

        if not isinstance(document, dict):
            raise LocalConfigurationError(
                f"Orion's local {kind} configuration is invalid."
            )

        return document

    def write(self, kind, document):

        if not isinstance(document, dict):
            raise LocalConfigurationError(
                f"Orion's local {kind} configuration is invalid."
            )

        with self._lock:
            try:
                self._write_atomic(
                    self.local_path(kind),
                    document,
                )
            except OSError as error:
                raise LocalConfigurationError(
                    f"Orion could not save its local {kind} configuration."
                ) from error

    def migrate_all(self):

        return {
            kind: self.ensure(kind)
            for kind in self.KINDS
        }

    def prepare_public_defaults(self):

        self.migrate_all()
        originals = {
            kind: (
                self.legacy_path(kind).read_bytes()
                if self.legacy_path(kind).is_file()
                else None
            )
            for kind in self.KINDS
        }

        try:
            for kind, definition in self.KINDS.items():
                self._write_atomic(
                    self.legacy_path(kind),
                    definition["default"],
                )
        except OSError as error:
            for kind, original in originals.items():
                path = self.legacy_path(kind)

                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    temporary = path.with_suffix(
                        path.suffix + ".rollback"
                    )
                    temporary.write_bytes(original)
                    os.replace(temporary, path)

            raise LocalConfigurationError(
                "Orion could not prepare its public defaults."
            ) from error


local_configuration = LocalConfiguration()


def services_config_path():

    return local_configuration.ensure("services")


def providers_config_path():

    return local_configuration.ensure("providers")


def media_config_path():

    return local_configuration.ensure("media")
