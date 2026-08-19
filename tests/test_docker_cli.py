import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.docker_cli import docker_executable


print("=" * 60)
print("DOCKER CLI RESOLUTION TEST")
print("=" * 60)
print()


original_override = os.environ.get(
    "ORION_DOCKER_CLI"
)

try:

    with TemporaryDirectory() as directory:

        docker_path = (
            Path(directory)
            / "docker.exe"
        )

        docker_path.write_bytes(b"")

        os.environ["ORION_DOCKER_CLI"] = (
            str(docker_path)
        )

        docker_executable.cache_clear()

        assert (
            Path(docker_executable())
            == docker_path.resolve()
        )

        print("✓ Explicit Docker CLI path resolved")

finally:

    if original_override is None:

        os.environ.pop(
            "ORION_DOCKER_CLI",
            None,
        )

    else:

        os.environ["ORION_DOCKER_CLI"] = (
            original_override
        )

    docker_executable.cache_clear()


original_local_app_data = os.environ.get(
    "LOCALAPPDATA"
)

try:

    with TemporaryDirectory() as directory:

        local_docker_path = (
            Path(directory)
            / "Programs"
            / "DockerDesktop"
            / "resources"
            / "bin"
            / "docker.exe"
        )

        local_docker_path.parent.mkdir(
            parents=True,
        )

        local_docker_path.write_bytes(b"")

        os.environ["LOCALAPPDATA"] = directory

        docker_executable.cache_clear()

        with patch(
            "app.docker_cli.shutil.which",
            return_value=None,
        ):

            assert (
                Path(docker_executable())
                == local_docker_path.resolve()
            )

        print("✓ Per-user Docker Desktop path resolved")

finally:

    if original_local_app_data is None:

        os.environ.pop(
            "LOCALAPPDATA",
            None,
        )

    else:

        os.environ["LOCALAPPDATA"] = (
            original_local_app_data
        )

    docker_executable.cache_clear()


try:

    with TemporaryDirectory() as directory:

        home_docker_path = (
            Path(directory)
            / "AppData"
            / "Local"
            / "Programs"
            / "DockerDesktop"
            / "resources"
            / "bin"
            / "docker.exe"
        )

        home_docker_path.parent.mkdir(
            parents=True,
        )

        home_docker_path.write_bytes(b"")

        os.environ.pop(
            "LOCALAPPDATA",
            None,
        )

        docker_executable.cache_clear()

        with (
            patch(
                "app.docker_cli.Path.home",
                return_value=Path(directory),
            ),
            patch(
                "app.docker_cli.shutil.which",
                return_value=None,
            ),
        ):

            assert (
                Path(docker_executable())
                == home_docker_path.resolve()
            )

        print("✓ Docker path resolved without LOCALAPPDATA")

finally:

    if original_local_app_data is not None:

        os.environ["LOCALAPPDATA"] = (
            original_local_app_data
        )

    docker_executable.cache_clear()


assert docker_executable()

print("✓ Docker CLI fallback remains available")
print()
print("✓ Docker CLI resolution test passed")
