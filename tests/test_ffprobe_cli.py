import os
from pathlib import Path
from tempfile import TemporaryDirectory

from app import ffprobe_cli


print("=" * 60)
print("FFPROBE CLI TEST")
print("=" * 60)
print()


original_environment = os.environ.copy()
original_which = ffprobe_cli.shutil.which

try:

    with TemporaryDirectory() as temporary_directory:

        root = Path(temporary_directory)
        configured_executable = (
            root / "configured-ffprobe.exe"
        )
        configured_executable.touch()

        os.environ["ORION_FFPROBE"] = str(
            configured_executable
        )
        ffprobe_cli.ffprobe_executable.cache_clear()

        assert (
            ffprobe_cli.ffprobe_executable()
            == str(configured_executable.resolve())
        )

        print("✓ Explicit FFprobe path supported")

        del os.environ["ORION_FFPROBE"]

        local_app_data = root / "LocalAppData"
        winget_link = (
            local_app_data
            / "Microsoft"
            / "WinGet"
            / "Links"
            / "ffprobe.exe"
        )
        winget_link.parent.mkdir(
            parents=True
        )
        winget_link.touch()

        os.environ["LOCALAPPDATA"] = str(
            local_app_data
        )
        ffprobe_cli.shutil.which = (
            lambda *args, **kwargs: None
        )
        ffprobe_cli.ffprobe_executable.cache_clear()

        assert (
            ffprobe_cli.ffprobe_executable()
            == str(winget_link.resolve())
        )

        print("✓ Per-user WinGet install resolved")

finally:

    os.environ.clear()
    os.environ.update(original_environment)
    ffprobe_cli.shutil.which = original_which
    ffprobe_cli.ffprobe_executable.cache_clear()

print()
print("✓ FFprobe CLI test passed")
