import os
from pathlib import Path
from tempfile import TemporaryDirectory

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


assert docker_executable()

print("✓ Docker CLI fallback remains available")
print()
print("✓ Docker CLI resolution test passed")
