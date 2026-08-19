import json
import re
import subprocess
import threading
import time

from app.docker_cli import docker_executable


class ContainerUpdateStatus:

    CACHE_SECONDS = 6 * 60 * 60

    CONTAINERS = (
        {
            "name": "AIOStreams",
            "slug": "aiostreams",
            "container": "aiostreams",
            "image": "ghcr.io/viren070/aiostreams:latest",
        },
        {
            "name": "UsenetStreamer",
            "slug": "usenetstreamer",
            "container": "usenetstreamer",
            "image": "gavpyro/usenetstreamer:latest",
        },
    )

    def __init__(
        self,
        command_runner=None,
        cache_seconds=None,
    ):

        self.command_runner = (
            command_runner
            or self._run_command
        )

        self.cache_seconds = (
            self.CACHE_SECONDS
            if cache_seconds is None
            else cache_seconds
        )

        self._cache = None
        self._cache_time = 0.0
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

        result = subprocess.run(
            command,
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

    @staticmethod
    def _digest_from_reference(reference):

        if not reference or "@" not in reference:

            return None

        digest = reference.rsplit("@", 1)[1].strip()

        if digest.startswith("sha256:"):

            return digest

        return None

    def _installed_digest(self, image):

        output = self.command_runner(
            [
                docker_executable(),
                "image",
                "inspect",
                image,
                "--format={{json .RepoDigests}}",
            ],
            timeout=10,
        )

        references = json.loads(output.strip())

        if not references:

            return None

        for reference in references:

            digest = self._digest_from_reference(
                reference
            )

            if digest:

                return digest

        return None

    def _registry_digest(self, image):

        output = self.command_runner(
            [
                docker_executable(),
                "buildx",
                "imagetools",
                "inspect",
                image,
            ],
            timeout=30,
        )

        match = re.search(
            r"^Digest:\s*(sha256:[0-9a-f]{64})\s*$",
            output,
            flags=re.MULTILINE | re.IGNORECASE,
        )

        if match is None:

            raise RuntimeError(
                "The registry digest was not returned."
            )

        return match.group(1).lower()

    def _check_container(self, definition):

        result = dict(definition)

        result.update(
            {
                "status": "unable",
                "update_available": None,
                "installed_digest": None,
                "registry_digest": None,
                "message": "Unable to check for updates.",
            }
        )

        try:

            installed_digest = (
                self._installed_digest(
                    definition["image"]
                )
            )

            if installed_digest is None:

                result.update(
                    {
                        "status": "not-installed",
                        "message": (
                            "The container image is "
                            "not installed locally."
                        ),
                    }
                )

                return result

            registry_digest = (
                self._registry_digest(
                    definition["image"]
                )
            )

            update_available = (
                installed_digest
                != registry_digest
            )

            result.update(
                {
                    "status": (
                        "available"
                        if update_available
                        else "current"
                    ),
                    "update_available": (
                        update_available
                    ),
                    "installed_digest": (
                        installed_digest
                    ),
                    "registry_digest": (
                        registry_digest
                    ),
                    "message": (
                        "Update available."
                        if update_available
                        else "Up to date."
                    ),
                }
            )

        except (
            json.JSONDecodeError,
            OSError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as error:

            result["error"] = str(error)

        return result

    def get_all(self, force=False):

        now = time.monotonic()

        with self._cache_lock:

            cache_is_current = (
                self._cache is not None
                and (
                    now - self._cache_time
                    < self.cache_seconds
                )
            )

            if cache_is_current and not force:

                return [
                    dict(item)
                    for item in self._cache
                ]

        results = [
            self._check_container(definition)
            for definition in self.CONTAINERS
        ]

        with self._cache_lock:

            self._cache = [
                dict(item)
                for item in results
            ]

            self._cache_time = (
                time.monotonic()
            )

        return results

    def clear_cache(self):

        with self._cache_lock:

            self._cache = None
            self._cache_time = 0.0
