import os
import shutil
from functools import lru_cache
from pathlib import Path

try:

    import winreg

except ImportError:

    winreg = None


def _registry_value(root, key_path, name):

    if winreg is None:

        return None

    try:

        with winreg.OpenKey(
            root,
            key_path,
        ) as key:

            value, _ = winreg.QueryValueEx(
                key,
                name,
            )

            return os.path.expandvars(
                str(value)
            )

    except OSError:

        return None


def _candidate_paths():

    configured = os.environ.get(
        "ORION_DOCKER_CLI"
    )

    if configured:

        yield Path(configured.strip('"'))

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if local_app_data:

        yield (
            Path(local_app_data)
            / "Programs"
            / "DockerDesktop"
            / "resources"
            / "bin"
            / "docker.exe"
        )

    program_files = {
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramW6432"),
        r"C:\Program Files",
    }

    for root in program_files:

        if root:

            yield (
                Path(root)
                / "Docker"
                / "Docker"
                / "resources"
                / "bin"
                / "docker.exe"
            )

    program_data = os.environ.get(
        "ProgramData",
        r"C:\ProgramData",
    )

    yield (
        Path(program_data)
        / "DockerDesktop"
        / "version-bin"
        / "docker.exe"
    )

    uninstall_key = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion"
        r"\Uninstall\Docker Desktop"
    )

    if winreg is not None:

        for root in (
            winreg.HKEY_LOCAL_MACHINE,
            winreg.HKEY_CURRENT_USER,
        ):

            install_location = _registry_value(
                root,
                uninstall_key,
                "InstallLocation",
            )

            if install_location:

                yield (
                    Path(install_location)
                    / "resources"
                    / "bin"
                    / "docker.exe"
                )

        registry_paths = [
            _registry_value(
                winreg.HKEY_LOCAL_MACHINE,
                (
                    r"SYSTEM\CurrentControlSet\Control"
                    r"\Session Manager\Environment"
                ),
                "Path",
            ),
            _registry_value(
                winreg.HKEY_CURRENT_USER,
                "Environment",
                "Path",
            ),
        ]

        registry_path = os.pathsep.join(
            value
            for value in registry_paths
            if value
        )

        if registry_path:

            resolved = shutil.which(
                "docker.exe",
                path=registry_path,
            )

            if resolved:

                yield Path(resolved)


@lru_cache(maxsize=1)
def docker_executable():

    configured = os.environ.get(
        "ORION_DOCKER_CLI"
    )

    if not configured and (
        shutil.which("docker.exe")
        or shutil.which("docker")
    ):

        return "docker"

    for candidate in _candidate_paths():

        try:

            if candidate.is_file():

                return str(candidate.resolve())

        except OSError:

            continue

    return "docker"
