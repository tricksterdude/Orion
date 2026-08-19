import re
import subprocess
import threading

from app.docker_cli import docker_executable


class ServiceController:

    ALLOWED_ACTIONS = {
        "restart": "restarted",
        "stop": "stopped",
    }

    def __init__(
        self,
        command_runner=None,
        docker_command=None,
    ):

        self.command_runner = (
            command_runner
            or self._run_command
        )

        self.docker_command = (
            docker_command
            or docker_executable
        )

        self._lock = threading.Lock()

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

        try:

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

        except FileNotFoundError as error:

            raise RuntimeError(
                "Docker CLI could not be found. "
                "Restart Orion after Docker Desktop "
                "is installed or set ORION_DOCKER_CLI."
            ) from error

        if result.returncode != 0:

            message = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Docker did not complete the request."
            )

            raise RuntimeError(message)

        return result.stdout.strip()

    @staticmethod
    def _valid_container(container):

        return re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]*",
            str(container or ""),
        ) is not None

    def control(self, action, container):

        completed_action = (
            self.ALLOWED_ACTIONS.get(action)
        )

        if completed_action is None:

            return {
                "ok": False,
                "status": "invalid",
                "message": (
                    "That service action is not allowed."
                ),
            }

        if not self._valid_container(container):

            return {
                "ok": False,
                "status": "invalid",
                "message": (
                    "The configured Docker container "
                    "name is invalid."
                ),
            }

        try:

            with self._lock:

                self.command_runner(
                    [
                        self.docker_command(),
                        action,
                        container,
                    ],
                    timeout=60,
                    cwd=None,
                )

        except (
            OSError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as error:

            return {
                "ok": False,
                "status": "failed",
                "message": (
                    f"Orion could not {action} "
                    f"{container}: {error}"
                ),
            }

        return {
            "ok": True,
            "status": completed_action,
            "message": (
                f"{container} was {completed_action} "
                "successfully."
            ),
        }
