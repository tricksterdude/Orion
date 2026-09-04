import copy
import json
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import psutil

from app.audio.spatial_processors import SpatialAudioProcessors
from app.audio.windows_output import WindowsAudioOutput
from app.display.adapter import DisplayAdapter
from app.docker_cli import docker_executable
from app.ffprobe_cli import ffprobe_executable
from app.stremio_controller import StremioController
from config.version import VERSION


class SystemDiagnostics:

    CACHE_SECONDS = 20

    STATUS_LABELS = {
        "healthy": "Healthy",
        "warning": "Warning",
        "action_required": "Action required",
    }

    CONFIG_FILES = (
        ("settings.json", "application settings"),
        ("services.json", "service configuration"),
        ("providers.json", "playback providers"),
    )

    def __init__(
        self,
        service_status=None,
        stremio_controller=None,
        project_root=None,
        docker_resolver=None,
        ffprobe_resolver=None,
        display_factory=None,
        audio_output_factory=None,
        spatial_processors_factory=None,
        command_runner=None,
        process_iter=None,
        clock=None,
    ):

        self.service_status = service_status
        self.stremio = (
            stremio_controller
            or StremioController()
        )
        self.project_root = (
            Path(project_root)
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        self.docker_resolver = (
            docker_resolver or docker_executable
        )
        self.ffprobe_resolver = (
            ffprobe_resolver or ffprobe_executable
        )
        self.display_factory = (
            display_factory or DisplayAdapter
        )
        self.audio_output_factory = (
            audio_output_factory or WindowsAudioOutput
        )
        self.spatial_processors_factory = (
            spatial_processors_factory
            or SpatialAudioProcessors
        )
        self.command_runner = (
            command_runner or self._run_command
        )
        self.process_iter = (
            process_iter or psutil.process_iter
        )
        self.clock = clock or time.monotonic

        self._cache = None
        self._cached_at = 0
        self._cache_lock = threading.Lock()

    @staticmethod
    def _run_command(command, timeout):

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

        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )

    @staticmethod
    def _check(
        check_id,
        name,
        status,
        summary,
        guidance,
        detail=None,
        report_detail=None,
    ):

        return {
            "id": check_id,
            "name": name,
            "status": status,
            "label": SystemDiagnostics.STATUS_LABELS[
                status
            ],
            "summary": summary,
            "guidance": guidance,
            "detail": detail,
            "report_detail": report_detail,
        }

    def _safe_check(self, check_id, name, function):

        try:

            return function()

        except Exception:

            return self._check(
                check_id,
                name,
                "action_required",
                f"Orion could not complete the {name.lower()} check.",
                (
                    "Restart Orion and run diagnostics again. "
                    "If the problem remains, use the safe "
                    "diagnostic report when asking for help."
                ),
            )

    @staticmethod
    def _valid_config(filename, data):

        if not isinstance(data, dict):

            return False

        if filename == "settings.json":

            application = data.get("application")

            return (
                isinstance(application, str)
                and bool(application.strip())
            )

        if filename == "providers.json":

            providers = data.get("providers")

            return (
                isinstance(providers, list)
                and all(
                    isinstance(provider, str)
                    and provider.strip()
                    for provider in providers
                )
            )

        if filename == "services.json":

            services = data.get("services")

            if not isinstance(services, list):

                return False

            for service in services:

                if not isinstance(service, dict):

                    return False

                if not all(
                    isinstance(service.get(field), str)
                    and service[field].strip()
                    for field in (
                        "name",
                        "container",
                        "url",
                    )
                ):

                    return False

                port = service.get("port")

                if (
                    isinstance(port, bool)
                    or not isinstance(port, int)
                    or not 1 <= port <= 65535
                ):

                    return False

            return True

        return False

    def _config_check(self):

        problems = []

        for filename, description in self.CONFIG_FILES:

            path = self.project_root / "config" / filename

            if filename in {
                "services.json",
                "providers.json",
            }:
                local_path = (
                    self.project_root
                    / "data"
                    / "profile"
                    / filename
                )

                if local_path.is_file():
                    path = local_path

            try:

                with path.open(
                    "r",
                    encoding="utf-8",
                ) as file:

                    data = json.load(file)

            except (OSError, json.JSONDecodeError):

                problems.append(description)
                continue

            if not self._valid_config(
                filename,
                data,
            ):

                problems.append(description)

        if problems:

            return self._check(
                "configuration",
                "Configuration files",
                "action_required",
                "One or more Orion configuration files are unavailable or invalid.",
                (
                    "Restore the affected configuration from a "
                    "known-good copy before restarting Orion."
                ),
                "Affected areas: " + ", ".join(problems),
            )

        return self._check(
            "configuration",
            "Configuration files",
            "healthy",
            "Orion's configuration files are readable and valid JSON.",
            "No action is required.",
            "Configuration values are never included in this check.",
        )

    def _docker_check(self):

        executable = self.docker_resolver()

        try:

            result = self.command_runner(
                [
                    executable,
                    "version",
                    "--format",
                    "{{.Server.Version}}",
                ],
                timeout=5,
            )

        except (OSError, subprocess.SubprocessError):

            result = None

        if result is None or result.returncode != 0:

            return self._check(
                "docker",
                "Docker engine",
                "action_required",
                "Orion cannot communicate with Docker Desktop.",
                (
                    "Start Docker Desktop, wait for it to finish "
                    "starting, then refresh diagnostics."
                ),
            )

        return self._check(
            "docker",
            "Docker engine",
            "healthy",
            "Docker Desktop is available to Orion.",
            "No action is required.",
        )

    def _ffprobe_check(self):

        executable = self.ffprobe_resolver()

        try:

            result = self.command_runner(
                [executable, "-version"],
                timeout=5,
            )

        except (OSError, subprocess.SubprocessError):

            result = None

        if result is None or result.returncode != 0:

            return self._check(
                "ffprobe",
                "Playback analysis",
                "action_required",
                "FFprobe is not available to Orion's background process.",
                (
                    "Install FFmpeg or set ORION_FFPROBE to the "
                    "full path of ffprobe.exe, then restart Orion."
                ),
            )

        return self._check(
            "ffprobe",
            "Playback analysis",
            "healthy",
            "FFprobe is available for playback metadata analysis.",
            "No action is required.",
        )

    def _display_check(self):

        mode = self.display_factory().current_mode()

        if mode is None:

            return self._check(
                "display",
                "Display control",
                "action_required",
                "Orion cannot read the current Windows display mode.",
                (
                    "Confirm the television is connected and "
                    "restart Orion in the signed-in Windows session."
                ),
            )

        return self._check(
            "display",
            "Display control",
            "healthy",
            "Orion can read the active display mode.",
            "No action is required.",
            (
                f"Current mode: {mode.width}x{mode.height} "
                f"at {mode.refresh} Hz."
            ),
        )

    def _configured_receiver(self):

        candidates = (
            self.project_root
            / "data"
            / "profile"
            / "media.json",
            self.project_root
            / "data"
            / "media_profile.json",
        )

        for path in candidates:

            try:

                document = json.loads(
                    path.read_text(encoding="utf-8")
                )
                receiver = (
                    document.get("audio", {})
                    .get("receiver")
                )

                if isinstance(receiver, str) and receiver.strip():

                    return receiver.strip()

            except (OSError, ValueError, TypeError):

                continue

        return None

    @staticmethod
    def _device_key(value):

        return re.sub(
            r"[^a-z0-9]+",
            "",
            str(value or "").casefold(),
        )

    def _audio_check(self):

        try:

            endpoint = (
                self.audio_output_factory()
                .default_endpoint()
            )

        except Exception:

            return self._check(
                "audio_output",
                "Windows audio output",
                "warning",
                "Orion could not identify the default Windows audio output.",
                (
                    "Confirm a playback device is enabled in Windows, "
                    "then refresh diagnostics. Orion will not change it."
                ),
            )

        detail = f"Default output: {endpoint.name}."
        processor_report = "No optional spatial processor was detected."

        try:

            processors = (
                self.spatial_processors_factory()
                .installed()
            )
            processor_names = [
                processor["name"]
                for processor in processors
                if processor.get("name")
            ]

            if processor_names:

                joined = ", ".join(processor_names)
                detail += f" Spatial processors: {joined}."
                processor_report = (
                    f"Optional spatial processors detected: {joined}."
                )

            else:

                detail += " Spatial processors: none detected."

        except Exception:

            detail += " Spatial processor availability was not observed."
            processor_report = (
                "Optional spatial processor availability was not observed."
            )

        if endpoint.form_factor:

            detail += f" Type: {endpoint.form_factor}."

        if not endpoint.active:

            return self._check(
                "audio_output",
                "Windows audio output",
                "warning",
                "The default Windows audio output is not active.",
                (
                    "Select the intended HDMI or receiver output in "
                    "Windows before playback."
                ),
                detail,
                (
                    "The default audio endpoint is not active. "
                    + processor_report
                ),
            )

        receiver = self._configured_receiver()
        receiver_key = self._device_key(receiver)
        endpoint_key = self._device_key(endpoint.name)
        unconfigured = receiver_key in {
            "",
            "notconfigured",
            "none",
        }

        if unconfigured:

            return self._check(
                "audio_output",
                "Windows audio output",
                "warning",
                (
                    "The default Windows audio output is active, but "
                    "no receiver is identified in Orion's profile."
                ),
                (
                    "Review System Setup and describe the intended "
                    "receiver or audio output."
                ),
                detail,
                (
                    "The default audio endpoint is active. "
                    + processor_report
                ),
            )

        matches = (
            receiver_key in endpoint_key
            or endpoint_key in receiver_key
        )

        if matches:

            return self._check(
                "audio_output",
                "Windows audio output",
                "healthy",
                "The configured receiver is the default Windows audio output.",
                "No action is required.",
                detail,
                (
                    "The configured receiver matches the active default "
                    "endpoint. "
                    + processor_report
                ),
            )

        return self._check(
            "audio_output",
            "Windows audio output",
            "warning",
            (
                "The default Windows audio output does not match "
                "Orion's configured receiver."
            ),
            (
                "Select the intended HDMI receiver output in Windows "
                "or correct the receiver description in System Setup."
            ),
            detail,
            (
                "The configured receiver does not match the default "
                "endpoint. "
                + processor_report
            ),
        )

    @staticmethod
    def _is_orion_command(command_line):

        for part in command_line or []:

            filename = (
                str(part)
                .strip('"')
                .replace("/", "\\")
                .rsplit("\\", 1)[-1]
                .lower()
            )

            if filename in {
                "background.py",
                "main.py",
            }:

                return True

        return False

    def _instance_check(self):

        matches = []

        for process in self.process_iter(
            ["pid", "ppid", "name", "cmdline"]
        ):

            try:

                info = process.info

                if not self._is_orion_command(
                    info.get("cmdline")
                ):

                    continue

                matches.append(
                    (
                        int(info.get("pid")),
                        int(info.get("ppid") or 0),
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
                psutil.Error,
            ):

                continue

        process_ids = {
            process_id
            for process_id, _ in matches
        }

        root_instances = [
            process_id
            for process_id, parent_id in matches
            if parent_id not in process_ids
        ]

        if len(root_instances) > 1:

            return self._check(
                "single_instance",
                "Orion runtime",
                "action_required",
                "More than one independent Orion runtime appears to be active.",
                (
                    "Close the extra Orion instance, then restart "
                    "Orion once from its normal shortcut."
                ),
                f"Independent runtime trees detected: {len(root_instances)}.",
            )

        if not root_instances:

            return self._check(
                "single_instance",
                "Orion runtime",
                "warning",
                "The web server is running, but its background process could not be confirmed.",
                (
                    "If playback monitoring is not working, "
                    "restart Orion from its normal shortcut."
                ),
            )

        return self._check(
            "single_instance",
            "Orion runtime",
            "healthy",
            "One independent Orion runtime is active.",
            "No action is required.",
        )

    def _stremio_check(self):

        if not self.stremio.is_running():

            try:

                installed = self.stremio.executable.is_file()

            except OSError:

                installed = False

            if installed:

                return self._check(
                    "stremio",
                    "AIOStreams detection",
                    "healthy",
                    "Stremio is installed and ready to be launched by Orion.",
                    (
                        "Use Launch Stremio on the AIOStreams "
                        "service page before playback."
                    ),
                )

            return self._check(
                "stremio",
                "AIOStreams detection",
                "action_required",
                "Orion cannot find the Stremio application.",
                (
                    "Install Stremio in the current Windows "
                    "account, then restart Orion."
                ),
            )

        status = self.stremio.status()

        if status.get("ready"):

            return self._check(
                "stremio",
                "AIOStreams detection",
                "healthy",
                "AIOStreams playback detection is ready.",
                "No action is required.",
            )

        return self._check(
            "stremio",
            "AIOStreams detection",
            "action_required",
            "Stremio is open without Orion playback detection.",
            (
                "Close Stremio, then launch it from the "
                "AIOStreams service page."
            ),
        )

    def _service_check(self, services):

        if services is None:

            if self.service_status is None:

                services = []

            else:

                services = self.service_status.get_all()

        total = len(services)
        healthy = sum(
            1
            for service in services
            if service.get("healthy")
        )

        if total == 0:

            return self._check(
                "services",
                "Configured services",
                "warning",
                "No Docker services are configured in Orion.",
                "Add the services Orion should monitor from the homepage.",
            )

        if healthy != total:

            return self._check(
                "services",
                "Configured services",
                "warning",
                f"{healthy} of {total} configured services are responding.",
                (
                    "Open the affected service pages and confirm "
                    "their containers are running."
                ),
            )

        return self._check(
            "services",
            "Configured services",
            "healthy",
            f"All {total} configured services are responding.",
            "No action is required.",
        )

    def run(self, services=None, force=False):

        now = self.clock()

        with self._cache_lock:

            if (
                not force
                and self._cache is not None
                and now - self._cached_at
                < self.CACHE_SECONDS
            ):

                return copy.deepcopy(self._cache)

        tasks = (
            (
                "configuration",
                "Configuration files",
                self._config_check,
            ),
            ("docker", "Docker engine", self._docker_check),
            (
                "ffprobe",
                "Playback analysis",
                self._ffprobe_check,
            ),
            ("display", "Display control", self._display_check),
            (
                "audio_output",
                "Windows audio output",
                self._audio_check,
            ),
            (
                "single_instance",
                "Orion runtime",
                self._instance_check,
            ),
            (
                "stremio",
                "AIOStreams detection",
                self._stremio_check,
            ),
            (
                "services",
                "Configured services",
                lambda: self._service_check(services),
            ),
        )

        with ThreadPoolExecutor(
            max_workers=len(tasks)
        ) as executor:

            futures = [
                executor.submit(
                    self._safe_check,
                    check_id,
                    name,
                    function,
                )
                for check_id, name, function in tasks
            ]

            checks = [
                future.result()
                for future in futures
            ]

        counts = {
            status: sum(
                1
                for check in checks
                if check["status"] == status
            )
            for status in self.STATUS_LABELS
        }

        if counts["action_required"]:

            status = "action_required"

        elif counts["warning"]:

            status = "warning"

        else:

            status = "healthy"

        snapshot = {
            "status": status,
            "label": self.STATUS_LABELS[status],
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "counts": counts,
            "checks": checks,
        }

        with self._cache_lock:

            self._cache = copy.deepcopy(snapshot)
            self._cached_at = now

        return snapshot

    @staticmethod
    def _redact(text):

        text = str(text)
        text = re.sub(
            r"https?://[^\s]+",
            "[redacted-url]",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"[A-Za-z]:\\Users\\[^\\\s]+",
            r"C:\\Users\\[redacted]",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            (
                r"(?i)(api[_ -]?key|token|password|secret)"
                r"\s*[:=]\s*[^\s,;]+"
            ),
            r"\1=[redacted]",
            text,
        )
        return text

    def report(self, snapshot):

        lines = [
            "ORION SAFE DIAGNOSTIC REPORT",
            f"Version: {VERSION}",
            f"Generated: {snapshot['generated_at']}",
            f"Overall status: {snapshot['label']}",
            "",
            (
                "Privacy: configuration values, credentials, "
                "account names, host addresses, stream URLs, "
                "and playback history are excluded."
            ),
            "",
            "CHECKS",
        ]

        for check in snapshot["checks"]:

            lines.append(
                f"[{check['label'].upper()}] "
                f"{check['name']}: {check['summary']}"
            )

            report_detail = check.get("report_detail")

            if report_detail is None:

                report_detail = check.get("detail")

            if report_detail:

                lines.append(
                    f"  Detail: {report_detail}"
                )

            if check["status"] != "healthy":

                lines.append(
                    f"  Suggested action: {check['guidance']}"
                )

        return self._redact(
            "\n".join(lines) + "\n"
        )
