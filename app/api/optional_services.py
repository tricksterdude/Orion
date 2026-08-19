import json
import subprocess
import threading
import zipfile
from datetime import datetime
from pathlib import Path

from app.docker_cli import docker_executable


class OptionalServiceManager:

    OPTIONAL_SERVICES = {
        "nzbhydra2": {
            "name": "NZBHydra2",
            "slug": "nzbhydra2",
            "container": "nzbhydra2",
            "compose_service": "hydra",
            "compose_folder": Path(
                r"C:\usenet-stack"
            ),
            "compose_file": Path(
                r"C:\usenet-stack"
                r"\docker-compose.yml"
            ),
            "config_folder": Path(
                r"C:\usenet-stack\hydra"
            ),
        },
    }

    def __init__(
        self,
        command_runner=None,
        backup_root=None,
        services_config=None,
        optional_services=None,
    ):

        self.command_runner = (
            command_runner
            or self._run_command
        )

        project_root = (
            Path(__file__).resolve().parents[2]
        )

        self.backup_root = Path(
            backup_root
            or (
                project_root
                / "data"
                / "service_backups"
            )
        )

        self.services_config = Path(
            services_config
            or (
                project_root
                / "config"
                / "services.json"
            )
        )

        self.optional_services = (
            optional_services
            or self.OPTIONAL_SERVICES
        )

        self._change_lock = threading.Lock()

    @staticmethod
    def _run_command(
        command,
        timeout,
        cwd=None,
    ):

        startupinfo = None
        creationflags = 0

        if hasattr(subprocess, "STARTUPINFO"):

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= (
                subprocess.STARTF_USESHOWWINDOW
            )

            creationflags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )

        if result.returncode != 0:

            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "The command failed."
            )

            raise RuntimeError(message)

        return result.stdout

    @staticmethod
    def _read_text(path):

        return Path(path).read_text(
            encoding="utf-8"
        )

    @staticmethod
    def _write_text(path, text):

        path = Path(path)

        temporary_path = path.with_name(
            f"{path.name}.orion.tmp"
        )

        temporary_path.write_text(
            text,
            encoding="utf-8",
        )

        temporary_path.replace(path)

    def _backup(self, definition):

        config_folder = Path(
            definition["config_folder"]
        )

        compose_file = Path(
            definition["compose_file"]
        )

        if not config_folder.is_dir():

            raise RuntimeError(
                "The service configuration folder "
                f"does not exist: {config_folder}"
            )

        if not compose_file.is_file():

            raise RuntimeError(
                "The Docker Compose file "
                f"does not exist: {compose_file}"
            )

        if not self.services_config.is_file():

            raise RuntimeError(
                "Orion's services configuration "
                "file does not exist."
            )

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )

        backup_path = (
            self.backup_root
            / (
                f"{definition['slug']}-"
                f"{timestamp}.zip"
            )
        )

        with zipfile.ZipFile(
            backup_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:

            for file_path in config_folder.rglob("*"):

                if not file_path.is_file():

                    continue

                relative_path = (
                    file_path.relative_to(
                        config_folder
                    )
                )

                archive.write(
                    file_path,
                    Path("config")
                    / relative_path,
                )

            archive.write(
                compose_file,
                Path("compose")
                / compose_file.name,
            )

            environment_file = (
                definition["compose_folder"]
                / ".env"
            )

            if environment_file.is_file():

                archive.write(
                    environment_file,
                    Path("compose")
                    / environment_file.name,
                )

            archive.write(
                self.services_config,
                Path("orion")
                / self.services_config.name,
            )

        return backup_path

    @staticmethod
    def _remove_compose_service(
        compose_text,
        service_name,
    ):

        lines = compose_text.splitlines(
            keepends=True
        )

        service_header = (
            f"  {service_name}:"
        )

        start_index = None

        for index, line in enumerate(lines):

            if (
                line.rstrip("\r\n")
                == service_header
            ):

                start_index = index
                break

        if start_index is None:

            raise RuntimeError(
                "The optional service was not "
                "found in the Docker Compose file."
            )

        end_index = len(lines)

        for index in range(
            start_index + 1,
            len(lines),
        ):

            stripped_line = (
                lines[index].rstrip("\r\n")
            )

            if (
                stripped_line.startswith("  ")
                and not stripped_line.startswith(
                    "    "
                )
                and stripped_line.endswith(":")
                and stripped_line.strip()
            ):

                end_index = index
                break

        updated_lines = (
            lines[:start_index]
            + lines[end_index:]
        )

        while (
            start_index > 0
            and start_index < len(updated_lines)
            and not updated_lines[
                start_index - 1
            ].strip()
            and not updated_lines[
                start_index
            ].strip()
        ):

            del updated_lines[
                start_index - 1
            ]

            start_index -= 1

        updated_text = "".join(
            updated_lines
        )

        if not updated_text.strip():

            raise RuntimeError(
                "Removing the service would leave "
                "an empty Docker Compose file."
            )

        return updated_text

    @staticmethod
    def _remove_orion_service(
        services_text,
        container_name,
    ):

        try:

            data = json.loads(
                services_text
            )

        except json.JSONDecodeError as error:

            raise RuntimeError(
                "Orion's services configuration "
                "is not valid JSON."
            ) from error

        services = data.get("services")

        if not isinstance(services, list):

            raise RuntimeError(
                "Orion's services configuration "
                "does not contain a services list."
            )

        remaining_services = [
            service
            for service in services
            if (
                service.get("container")
                != container_name
            )
        ]

        if (
            len(remaining_services)
            == len(services)
        ):

            raise RuntimeError(
                "The optional service was not "
                "found in Orion's configuration."
            )

        data["services"] = remaining_services

        return (
            json.dumps(
                data,
                indent=4,
            )
            + "\n"
        )

    def _validate_compose(
        self,
        definition,
        candidate_text,
    ):

        compose_folder = Path(
            definition["compose_folder"]
        )

        candidate_path = (
            compose_folder
            / ".orion-compose-candidate.yml"
        )

        try:

            candidate_path.write_text(
                candidate_text,
                encoding="utf-8",
            )

            self.command_runner(
                [
                    docker_executable(),
                    "compose",
                    "--project-directory",
                    str(compose_folder),
                    "-f",
                    str(candidate_path),
                    "config",
                    "--quiet",
                ],
                timeout=30,
                cwd=str(compose_folder),
            )

        finally:

            if candidate_path.exists():

                candidate_path.unlink()

    def _remove_container(self, definition):

        compose_folder = str(
            definition["compose_folder"]
        )

        self.command_runner(
            [
                docker_executable(),
                "compose",
                "--project-directory",
                compose_folder,
                "rm",
                "--stop",
                "--force",
                definition["compose_service"],
            ],
            timeout=120,
            cwd=compose_folder,
        )

    def _restore_container(self, definition):

        compose_folder = str(
            definition["compose_folder"]
        )

        self.command_runner(
            [
                docker_executable(),
                "compose",
                "--project-directory",
                compose_folder,
                "up",
                "-d",
                "--no-deps",
                definition["compose_service"],
            ],
            timeout=180,
            cwd=compose_folder,
        )

    def remove(self, slug):

        definition = self.optional_services.get(
            slug
        )

        if definition is None:

            return {
                "ok": False,
                "status": "unknown",
                "message": (
                    "That service cannot be "
                    "removed by Orion."
                ),
            }

        if not self._change_lock.acquire(
            blocking=False
        ):

            return {
                "ok": False,
                "status": "busy",
                "message": (
                    "Another service change "
                    "is already running."
                ),
            }

        backup_path = None
        container_removed = False

        compose_file = Path(
            definition["compose_file"]
        )

        original_compose = None
        original_services = None

        try:

            original_compose = self._read_text(
                compose_file
            )

            original_services = self._read_text(
                self.services_config
            )

            updated_compose = (
                self._remove_compose_service(
                    original_compose,
                    definition["compose_service"],
                )
            )

            updated_services = (
                self._remove_orion_service(
                    original_services,
                    definition["container"],
                )
            )

            self._validate_compose(
                definition,
                updated_compose,
            )

            backup_path = self._backup(
                definition
            )

            self._remove_container(
                definition
            )

            container_removed = True

            self._write_text(
                compose_file,
                updated_compose,
            )

            self._write_text(
                self.services_config,
                updated_services,
            )

            return {
                "ok": True,
                "status": "removed",
                "name": definition["name"],
                "slug": definition["slug"],
                "backup_path": str(
                    backup_path
                ),
                "config_preserved": True,
                "message": (
                    f"{definition['name']} was "
                    "removed successfully. Its "
                    "configuration folder was kept."
                ),
            }

        except Exception as error:

            restoration_error = None

            try:

                if original_compose is not None:

                    self._write_text(
                        compose_file,
                        original_compose,
                    )

                if original_services is not None:

                    self._write_text(
                        self.services_config,
                        original_services,
                    )

                if container_removed:

                    self._restore_container(
                        definition
                    )

            except Exception as restore_error:

                restoration_error = str(
                    restore_error
                )

            message = str(error)

            if restoration_error:

                message = (
                    f"{message} Automatic restoration "
                    f"also failed: {restoration_error}"
                )

            return {
                "ok": False,
                "status": "failed",
                "name": definition["name"],
                "slug": definition["slug"],
                "backup_path": (
                    str(backup_path)
                    if backup_path is not None
                    else None
                ),
                "message": message,
            }

        finally:

            self._change_lock.release()
