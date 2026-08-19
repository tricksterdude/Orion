import json
import os
import re
import threading
import zipfile
from datetime import datetime
from pathlib import Path

from app.api.service_names import service_slug


class ServiceRegistry:

    MAX_NAME_LENGTH = 80

    def __init__(
        self,
        services_config=None,
        backup_root=None,
    ):

        project_root = Path(__file__).resolve().parents[2]

        self.services_config = Path(
            services_config
            or project_root / "config" / "services.json"
        )

        self.backup_root = Path(
            backup_root
            or project_root
            / "data"
            / "service_registry_backups"
        )

        self._lock = threading.Lock()

    @staticmethod
    def _slug(value):

        return service_slug(value)

    @classmethod
    def _validate_name(cls, value):

        name = str(value or "").strip()

        if not name:

            raise ValueError(
                "A service name is required."
            )

        if len(name) > cls.MAX_NAME_LENGTH:

            raise ValueError(
                "The service name is too long."
            )

        if any(
            ord(character) < 32
            for character in name
        ):

            raise ValueError(
                "The service name contains invalid characters."
            )

        if not cls._slug(name):

            raise ValueError(
                "The service name is invalid."
            )

        return name

    @staticmethod
    def _validate_container(value):

        container = str(value or "").strip()

        if not container:

            raise ValueError(
                "A Docker container name is required."
            )

        if not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]*",
            container,
        ):

            raise ValueError(
                "The Docker container name is invalid."
            )

        return container

    @staticmethod
    def _validate_port(value):

        try:

            port = int(value)

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                "The service port is invalid."
            )

        if not 1 <= port <= 65535:

            raise ValueError(
                "The service port is invalid."
            )

        return port

    def _read_document(self):

        if not self.services_config.exists():

            return {
                "services": [],
            }

        text = self.services_config.read_text(
            encoding="utf-8"
        )

        document = json.loads(text)

        if not isinstance(document, dict):

            raise ValueError(
                "The Orion services configuration is invalid."
            )

        services = document.get("services")

        if not isinstance(services, list):

            raise ValueError(
                "The Orion services configuration is invalid."
            )

        return document

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
    def _write_atomic(path, text):

        path = Path(path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = path.with_name(
            f"{path.name}.tmp"
        )

        temporary_path.write_text(
            text,
            encoding="utf-8",
        )

        os.replace(
            temporary_path,
            path,
        )

    def _backup(self):

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d-%H%M%S-%f"
        )

        backup_path = (
            self.backup_root
            / f"services-{timestamp}.zip"
        )

        with zipfile.ZipFile(
            backup_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:

            if self.services_config.exists():

                archive.write(
                    self.services_config,
                    arcname="orion/services.json",
                )

        return backup_path

    @staticmethod
    def _result(
        status,
        message,
        service=None,
        backup=None,
    ):

        result = {
            "status": status,
            "message": message,
        }

        if service is not None:

            result["service"] = service

        if backup is not None:

            result["backup"] = str(backup)

        return result

    def add(
        self,
        candidate,
        display_name=None,
    ):

        if not isinstance(candidate, dict):

            return self._result(
                "invalid",
                "The selected Docker service is invalid.",
            )

        try:

            name = self._validate_name(
                display_name
                or candidate.get("name")
                or candidate.get("container")
            )

            container = self._validate_container(
                candidate.get("container")
            )

            port = self._validate_port(
                candidate.get("port")
            )

        except ValueError as error:

            return self._result(
                "invalid",
                str(error),
            )

        service = {
            "name": name,
            "container": container,
            "port": port,
            "url": f"http://localhost:{port}",
        }

        with self._lock:

            try:

                document = self._read_document()

            except (
                OSError,
                ValueError,
                json.JSONDecodeError,
            ) as error:

                return self._result(
                    "failed",
                    (
                        "Orion could not read its service "
                        f"configuration: {error}"
                    ),
                )

            services = document["services"]

            requested_slug = self._slug(name)
            requested_container = container.lower()

            for existing in services:

                if not isinstance(existing, dict):

                    continue

                existing_container = str(
                    existing.get("container") or ""
                ).strip().lower()

                try:

                    existing_port = int(
                        existing.get("port")
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    existing_port = None

                existing_slug = self._slug(
                    existing.get("name")
                )

                if (
                    existing_container
                    == requested_container
                    and existing_port == port
                ):

                    return self._result(
                        "exists",
                        (
                            f"{name} is already monitored "
                            "by Orion."
                        ),
                        service=existing,
                    )

                if existing_slug == requested_slug:

                    return self._result(
                        "exists",
                        (
                            "Another Orion service already "
                            f"uses the name {name}."
                        ),
                        service=existing,
                    )

            original_text = None

            if self.services_config.exists():

                try:

                    original_text = (
                        self.services_config.read_text(
                            encoding="utf-8"
                        )
                    )

                except OSError as error:

                    return self._result(
                        "failed",
                        (
                            "Orion could not read its service "
                            f"configuration: {error}"
                        ),
                    )

            try:

                backup_path = self._backup()

            except (
                OSError,
                zipfile.BadZipFile,
            ) as error:

                return self._result(
                    "failed",
                    (
                        "Orion could not back up its service "
                        f"configuration: {error}"
                    ),
                )

            services.append(service)

            try:

                self._write_atomic(
                    self.services_config,
                    self._serialise(document),
                )

                verified_document = self._read_document()

                if service not in verified_document["services"]:

                    raise ValueError(
                        "The saved service could not be verified."
                    )

            except (
                OSError,
                ValueError,
                json.JSONDecodeError,
            ) as error:

                try:

                    if original_text is None:

                        if self.services_config.exists():

                            self.services_config.unlink()

                    else:

                        self._write_atomic(
                            self.services_config,
                            original_text,
                        )

                except OSError:

                    pass

                return self._result(
                    "failed",
                    (
                        "Orion could not save the service. "
                        f"The previous configuration was restored: {error}"
                    ),
                    backup=backup_path,
                )

            return self._result(
                "added",
                (
                    f"{name} was added to Orion successfully."
                ),
                service=service,
                backup=backup_path,
            )
