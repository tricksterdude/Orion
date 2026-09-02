import os
import subprocess
from pathlib import Path

import psutil

from app.technical.stremio_probe import StremioProbe


class StremioController:

    DEBUG_ARGUMENTS = (
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
    )

    def __init__(
        self,
        probe=None,
        process_iter=None,
        process_launcher=None,
        executable=None,
    ):

        self.probe = probe or StremioProbe()
        self.process_iter = (
            process_iter or psutil.process_iter
        )
        self.process_launcher = (
            process_launcher or subprocess.Popen
        )
        self.executable = (
            Path(executable)
            if executable is not None
            else self.stremio_path()
        )

    @staticmethod
    def stremio_path():

        local_app_data = os.environ.get(
            "LOCALAPPDATA"
        )

        if not local_app_data:

            return Path()

        return (
            Path(local_app_data)
            / "Programs"
            / "Stremio"
            / "stremio-shell-ng.exe"
        )

    def is_running(self):

        try:

            processes = self.process_iter(
                ["name"]
            )

            for process in processes:

                try:

                    name = process.info.get(
                        "name"
                    )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                ):

                    continue

                if (
                    name
                    and "stremio-shell-ng"
                    in name.lower()
                ):

                    return True

        except (
            psutil.Error,
            OSError,
        ):

            return False

        return False

    def status(self):

        if self.probe.debugger_available():

            return {
                "state": "ready",
                "ready": True,
                "can_launch": False,
                "message": (
                    "AIOStreams playback detection "
                    "is ready."
                ),
            }

        if self.is_running():

            return {
                "state": "restart_required",
                "ready": False,
                "can_launch": False,
                "message": (
                    "Stremio is running without Orion "
                    "playback detection. Close Stremio, "
                    "then return here and launch it "
                    "with Orion."
                ),
            }

        try:

            installed = self.executable.is_file()

        except OSError:

            installed = False

        if not installed:

            return {
                "state": "unavailable",
                "ready": False,
                "can_launch": False,
                "message": (
                    "Orion could not find the Stremio "
                    "application."
                ),
            }

        return {
            "state": "stopped",
            "ready": False,
            "can_launch": True,
            "message": (
                "Launch Stremio with Orion to enable "
                "AIOStreams playback detection."
            ),
        }

    def launch(self):

        status = self.status()

        if status["ready"]:

            return {
                "ok": True,
                "message": status["message"],
            }

        if not status["can_launch"]:

            return {
                "ok": False,
                "message": status["message"],
            }

        environment = os.environ.copy()
        existing_arguments = environment.get(
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",
            "",
        ).strip()

        arguments = existing_arguments.split()

        for argument in self.DEBUG_ARGUMENTS:

            if argument not in arguments:

                arguments.append(argument)

        environment[
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"
        ] = " ".join(arguments)

        try:

            self.process_launcher(
                [str(self.executable)],
                env=environment,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0,
                ),
            )

        except (OSError, subprocess.SubprocessError):

            return {
                "ok": False,
                "message": (
                    "Orion could not launch Stremio."
                ),
            }

        return {
            "ok": True,
            "message": (
                "Stremio launched with AIOStreams "
                "playback detection enabled."
            ),
        }
