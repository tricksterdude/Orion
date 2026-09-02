import os
import shutil
from functools import lru_cache
from pathlib import Path

try:

    import winreg

except ImportError:

    winreg = None


def _registry_path():

    if winreg is None:

        return None

    values = []

    locations = (
        (
            winreg.HKEY_LOCAL_MACHINE,
            (
                r"SYSTEM\CurrentControlSet\Control"
                r"\Session Manager\Environment"
            ),
        ),
        (
            winreg.HKEY_CURRENT_USER,
            "Environment",
        ),
    )

    for root, key_path in locations:

        try:

            with winreg.OpenKey(
                root,
                key_path,
            ) as key:

                value, _ = winreg.QueryValueEx(
                    key,
                    "Path",
                )

                values.append(
                    os.path.expandvars(
                        str(value)
                    )
                )

        except OSError:

            continue

    if not values:

        return None

    return os.pathsep.join(values)


def _candidate_paths():

    configured = os.environ.get(
        "ORION_FFPROBE"
    )

    if configured:

        yield Path(configured.strip('"'))

    local_app_data_roots = []

    configured_local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if configured_local_app_data:

        local_app_data_roots.append(
            Path(configured_local_app_data)
        )

    local_app_data_roots.append(
        Path.home()
        / "AppData"
        / "Local"
    )

    for local_app_data in dict.fromkeys(
        local_app_data_roots
    ):

        yield (
            local_app_data
            / "Microsoft"
            / "WinGet"
            / "Links"
            / "ffprobe.exe"
        )

    program_files_roots = {
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramW6432"),
        r"C:\Program Files",
    }

    for root in program_files_roots:

        if root:

            yield (
                Path(root)
                / "ffmpeg"
                / "bin"
                / "ffprobe.exe"
            )

    chocolatey_install = os.environ.get(
        "ChocolateyInstall",
        r"C:\ProgramData\chocolatey",
    )

    yield (
        Path(chocolatey_install)
        / "bin"
        / "ffprobe.exe"
    )

    registry_path = _registry_path()

    if registry_path:

        resolved = shutil.which(
            "ffprobe.exe",
            path=registry_path,
        )

        if resolved:

            yield Path(resolved)


@lru_cache(maxsize=1)
def ffprobe_executable():

    configured = os.environ.get(
        "ORION_FFPROBE"
    )

    if not configured:

        resolved = (
            shutil.which("ffprobe.exe")
            or shutil.which("ffprobe")
        )

        if resolved:

            return str(Path(resolved).resolve())

    for candidate in _candidate_paths():

        try:

            if candidate.is_file():

                return str(candidate.resolve())

        except OSError:

            continue

    return "ffprobe"
