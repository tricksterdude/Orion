import json
import tempfile
import zipfile
from pathlib import Path

from app.api.optional_services import (
    OptionalServiceManager,
)


print("=" * 60)
print("OPTIONAL SERVICE MANAGEMENT TEST")
print("=" * 60)
print()

compose_text = """services:
  nzbdav:
    image: nzbdav:test

  hydra:
    image: linuxserver/nzbhydra2:latest
    container_name: nzbhydra2
    ports:
      - "5076:5076"
    volumes:
      - ./hydra:/config

  aiostreams:
    image: aiostreams:test
"""

services_data = {
    "services": [
        {
            "name": "NZBDAV",
            "container": "nzbdav",
            "port": 8500,
            "url": "http://localhost:8500",
        },
        {
            "name": "NZBHydra2",
            "container": "nzbhydra2",
            "port": 5076,
            "url": "http://localhost:5076",
        },
        {
            "name": "AIOStreams",
            "container": "aiostreams",
            "port": 3500,
            "url": "http://localhost:3500",
        },
    ]
}


with tempfile.TemporaryDirectory() as folder:

    root = Path(folder)
    compose_folder = root / "stack"
    compose_folder.mkdir()

    compose_file = (
        compose_folder
        / "docker-compose.yml"
    )

    compose_file.write_text(
        compose_text,
        encoding="utf-8",
    )

    environment_file = (
        compose_folder / ".env"
    )

    environment_file.write_text(
        "EXAMPLE=value\n",
        encoding="utf-8",
    )

    config_folder = (
        compose_folder / "hydra"
    )

    config_folder.mkdir()

    hydra_config = (
        config_folder / "settings.cfg"
    )

    hydra_config.write_text(
        "saved-settings",
        encoding="utf-8",
    )

    services_config = (
        root / "services.json"
    )

    services_config.write_text(
        json.dumps(
            services_data,
            indent=4,
        ),
        encoding="utf-8",
    )

    commands = []

    def command_runner(
        command,
        timeout,
        cwd=None,
    ):

        commands.append(
            {
                "command": command,
                "timeout": timeout,
                "cwd": cwd,
            }
        )

        return ""

    definitions = {
        "nzbhydra2": {
            "name": "NZBHydra2",
            "slug": "nzbhydra2",
            "container": "nzbhydra2",
            "compose_service": "hydra",
            "compose_folder": compose_folder,
            "compose_file": compose_file,
            "config_folder": config_folder,
        },
    }

    manager = OptionalServiceManager(
        command_runner=command_runner,
        backup_root=root / "backups",
        services_config=services_config,
        optional_services=definitions,
    )

    result = manager.remove(
        "nzbhydra2"
    )

    assert result["ok"] is True
    assert result["status"] == "removed"
    assert result["config_preserved"] is True

    print("✓ Optional service removed")

    updated_compose = (
        compose_file.read_text(
            encoding="utf-8"
        )
    )

    assert "  hydra:" not in updated_compose
    assert "nzbhydra2" not in updated_compose
    assert "  nzbdav:" in updated_compose
    assert "  aiostreams:" in updated_compose

    print("✓ Only the selected Compose service removed")

    updated_services = json.loads(
        services_config.read_text(
            encoding="utf-8"
        )
    )

    containers = {
        service["container"]
        for service
        in updated_services["services"]
    }

    assert "nzbhydra2" not in containers
    assert "nzbdav" in containers
    assert "aiostreams" in containers

    print("✓ Orion service entry removed")

    assert config_folder.is_dir()
    assert hydra_config.is_file()
    assert (
        hydra_config.read_text(
            encoding="utf-8"
        )
        == "saved-settings"
    )

    print("✓ Service configuration folder preserved")

    backup_path = Path(
        result["backup_path"]
    )

    assert backup_path.is_file()

    with zipfile.ZipFile(
        backup_path
    ) as archive:

        archived_files = set(
            archive.namelist()
        )

    assert "config/settings.cfg" in archived_files
    assert (
        "compose/docker-compose.yml"
        in archived_files
    )
    assert "compose/.env" in archived_files
    assert (
        "orion/services.json"
        in archived_files
    )

    print("✓ Configuration and definitions backed up")

    command_lists = [
        item["command"]
        for item in commands
    ]

    assert any(
        "config" in command
        and "--quiet" in command
        for command in command_lists
    )

    assert any(
        "rm" in command
        and "--stop" in command
        and "--force" in command
        and "hydra" in command
        for command in command_lists
    )

    print("✓ Compose validated before removal")


with tempfile.TemporaryDirectory() as folder:

    root = Path(folder)
    compose_folder = root / "stack"
    compose_folder.mkdir()

    compose_file = (
        compose_folder
        / "docker-compose.yml"
    )

    compose_file.write_text(
        compose_text,
        encoding="utf-8",
    )

    config_folder = (
        compose_folder / "hydra"
    )

    config_folder.mkdir()

    services_config = (
        root / "services.json"
    )

    original_services_text = json.dumps(
        services_data,
        indent=4,
    )

    services_config.write_text(
        original_services_text,
        encoding="utf-8",
    )

    def failing_runner(
        command,
        timeout,
        cwd=None,
    ):

        if (
            "config" in command
            and "--quiet" in command
        ):

            raise RuntimeError(
                "Compose validation failed."
            )

        return ""

    definitions = {
        "nzbhydra2": {
            "name": "NZBHydra2",
            "slug": "nzbhydra2",
            "container": "nzbhydra2",
            "compose_service": "hydra",
            "compose_folder": compose_folder,
            "compose_file": compose_file,
            "config_folder": config_folder,
        },
    }

    manager = OptionalServiceManager(
        command_runner=failing_runner,
        backup_root=root / "backups",
        services_config=services_config,
        optional_services=definitions,
    )

    result = manager.remove(
        "nzbhydra2"
    )

    assert result["ok"] is False
    assert result["status"] == "failed"

    assert (
        compose_file.read_text(
            encoding="utf-8"
        )
        == compose_text
    )

    assert json.loads(
        services_config.read_text(
            encoding="utf-8"
        )
    ) == services_data

    print("✓ Invalid Compose change rejected safely")
    print("✓ Original configuration preserved after failure")


manager = OptionalServiceManager(
    optional_services={},
)

unknown_result = manager.remove(
    "not-allowed"
)

assert unknown_result["ok"] is False
assert unknown_result["status"] == "unknown"

print("✓ Unknown service rejected safely")

print()
print("✓ Optional service management test passed")