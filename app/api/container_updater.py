import json
import subprocess
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

from app.docker_cli import docker_executable


class ContainerUpdater:

    HEALTH_TIMEOUT_SECONDS = 120
    HEALTH_POLL_SECONDS = 2

    CONTAINERS = {
        "aiostreams": {
            "name": "AIOStreams",
            "slug": "aiostreams",
            "container": "aiostreams",
            "service": "aiostreams",
            "image": (
                "ghcr.io/viren070/"
                "aiostreams:latest"
            ),
            "compose_folder": Path(
                r"C:\usenet-stack"
            ),
            "config_folder": Path(
                r"C:\usenet-stack\aiostreams\data"
            ),
        },
        "usenetstreamer": {
            "name": "UsenetStreamer",
            "slug": "usenetstreamer",
            "container": "usenetstreamer",
            "service": "usenetstreamer",
            "image": (
                "gavpyro/"
                "usenetstreamer:latest"
            ),
            "compose_folder": Path(
                r"C:\usenet-stack"
            ),
            "config_folder": Path(
                r"C:\usenet-stack"
                r"\usenetstreamer-config"
            ),
        },
    }

    def __init__(
        self,
        command_runner=None,
        backup_root=None,
        status_checker=None,
        sleep_function=None,
        monotonic_function=None,
        containers=None,
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
                / "container_update_backups"
            )
        )

        self.status_checker = status_checker

        self.sleep = (
            sleep_function
            or time.sleep
        )

        self.monotonic = (
            monotonic_function
            or time.monotonic
        )

        self.containers = (
            containers
            or self.CONTAINERS
        )

        self._update_lock = threading.Lock()

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
                or "Docker command failed."
            )

            raise RuntimeError(message)

        return result.stdout

    def _container_image_id(self, container):

        output = self.command_runner(
            [
                docker_executable(),
                "inspect",
                container,
                "--format={{.Image}}",
            ],
            timeout=15,
            cwd=None,
        )

        image_id = output.strip()

        if not image_id.startswith("sha256:"):

            raise RuntimeError(
                "The installed image ID "
                "could not be determined."
            )

        return image_id

    def _backup(self, definition):

        source = Path(
            definition["config_folder"]
        )

        compose_folder = Path(
            definition["compose_folder"]
        )

        if not source.is_dir():

            raise RuntimeError(
                "The configuration folder "
                f"does not exist: {source}"
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

            for file_path in source.rglob("*"):

                if not file_path.is_file():

                    continue

                relative_path = (
                    file_path.relative_to(source)
                )

                archive.write(
                    file_path,
                    Path("config")
                    / relative_path,
                )

            compose_files = []

            for pattern in (
                ".env",
                "compose.yml",
                "compose.yaml",
                "docker-compose.yml",
                "docker-compose.yaml",
            ):

                compose_path = (
                    compose_folder / pattern
                )

                if compose_path.is_file():

                    compose_files.append(
                        compose_path
                    )

            for compose_path in compose_files:

                archive.write(
                    compose_path,
                    Path("compose")
                    / compose_path.name,
                )

        return backup_path

    def _pull(self, definition):

        compose_folder = str(
            definition["compose_folder"]
        )

        self.command_runner(
            [
                docker_executable(),
                "compose",
                "--project-directory",
                compose_folder,
                "pull",
                definition["service"],
            ],
            timeout=300,
            cwd=compose_folder,
        )

    def _recreate(self, definition):

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
                "--force-recreate",
                definition["service"],
            ],
            timeout=180,
            cwd=compose_folder,
        )

    def _container_state(self, container):

        output = self.command_runner(
            [
                docker_executable(),
                "inspect",
                container,
                "--format={{json .State}}",
            ],
            timeout=15,
            cwd=None,
        )

        return json.loads(
            output.strip()
        )

    @staticmethod
    def _state_is_ready(state):

        if not state.get("Running"):

            return False

        health = state.get("Health")

        if not isinstance(health, dict):

            return True

        return (
            health.get("Status")
            == "healthy"
        )

    def _wait_until_ready(self, container):

        deadline = (
            self.monotonic()
            + self.HEALTH_TIMEOUT_SECONDS
        )

        last_state = None

        while self.monotonic() < deadline:

            last_state = self._container_state(
                container
            )

            if self._state_is_ready(last_state):

                return last_state

            if last_state.get("Status") in {
                "dead",
                "exited",
            }:

                break

            self.sleep(
                self.HEALTH_POLL_SECONDS
            )

        status = "unknown"

        if isinstance(last_state, dict):

            health = last_state.get("Health")

            if isinstance(health, dict):

                status = health.get(
                    "Status",
                    status,
                )

            else:

                status = last_state.get(
                    "Status",
                    status,
                )

        raise RuntimeError(
            "The updated container did not "
            f"become healthy. Status: {status}"
        )

    def _rollback(
        self,
        definition,
        previous_image_id,
    ):

        self.command_runner(
            [
                docker_executable(),
                "image",
                "tag",
                previous_image_id,
                definition["image"],
            ],
            timeout=30,
            cwd=None,
        )

        self._recreate(definition)

        self._wait_until_ready(
            definition["container"]
        )

    def update(self, slug):

        definition = self.containers.get(
            slug
        )

        if definition is None:

            return {
                "ok": False,
                "status": "unknown",
                "message": (
                    "That container cannot "
                    "be updated by Orion."
                ),
            }

        if not self._update_lock.acquire(
            blocking=False
        ):

            return {
                "ok": False,
                "status": "busy",
                "message": (
                    "Another container update "
                    "is already running."
                ),
            }

        backup_path = None
        previous_image_id = None
        recreated = False

        try:

            backup_path = self._backup(
                definition
            )

            previous_image_id = (
                self._container_image_id(
                    definition["container"]
                )
            )

            self._pull(definition)
            self._recreate(definition)
            recreated = True

            self._wait_until_ready(
                definition["container"]
            )

            if self.status_checker is not None:

                self.status_checker.clear_cache()

            return {
                "ok": True,
                "status": "updated",
                "name": definition["name"],
                "slug": definition["slug"],
                "backup_path": str(
                    backup_path
                ),
                "message": (
                    f"{definition['name']} "
                    "updated successfully."
                ),
            }

        except Exception as error:

            rollback_succeeded = False
            rollback_error = None

            if (
                recreated
                and previous_image_id
                is not None
            ):

                try:

                    self._rollback(
                        definition,
                        previous_image_id,
                    )

                    rollback_succeeded = True

                except Exception as error_rollback:

                    rollback_error = str(
                        error_rollback
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
                "rollback_succeeded": (
                    rollback_succeeded
                ),
                "rollback_error": (
                    rollback_error
                ),
                "message": str(error),
            }

        finally:

            self._update_lock.release()
