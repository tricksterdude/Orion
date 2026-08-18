import tempfile
import zipfile
from pathlib import Path

from app.api.container_updater import (
    ContainerUpdater,
)


print("=" * 60)
print("CONTROLLED CONTAINER UPDATE TEST")
print("=" * 60)
print()


class StatusChecker:

    def __init__(self):

        self.cleared = False

    def clear_cache(self):

        self.cleared = True


with tempfile.TemporaryDirectory() as temporary:

    root = Path(temporary)
    compose_folder = root / "stack"
    config_folder = compose_folder / "app-data"
    backup_folder = root / "backups"

    config_folder.mkdir(parents=True)

    (
        config_folder / "settings.json"
    ).write_text(
        '{"api_key": "preserved"}',
        encoding="utf-8",
    )

    (
        compose_folder / "compose.yml"
    ).write_text(
        "services:\n  example:\n",
        encoding="utf-8",
    )

    (
        compose_folder / ".env"
    ).write_text(
        "SECRET=preserved\n",
        encoding="utf-8",
    )

    definitions = {
        "example": {
            "name": "Example",
            "slug": "example",
            "container": "example",
            "service": "example",
            "image": "example/image:latest",
            "compose_folder": compose_folder,
            "config_folder": config_folder,
        }
    }

    commands = []

    def successful_runner(
        command,
        timeout,
        cwd=None,
    ):

        commands.append(list(command))

        if (
            command[0:2]
            == ["docker", "inspect"]
            and "{{.Image}}" in command[-1]
        ):

            return (
                "sha256:"
                + ("a" * 64)
            )

        if (
            command[0:2]
            == ["docker", "inspect"]
            and "{{json .State}}" in command[-1]
        ):

            return (
                '{"Running": true, '
                '"Status": "running", '
                '"Health": {'
                '"Status": "healthy"}}'
            )

        if command[0:2] == [
            "docker",
            "compose",
        ]:

            return ""

        raise AssertionError(
            f"Unexpected command: {command}"
        )

    status_checker = StatusChecker()

    updater = ContainerUpdater(
        command_runner=successful_runner,
        backup_root=backup_folder,
        status_checker=status_checker,
        containers=definitions,
    )

    result = updater.update("example")

    assert result["ok"] is True
    assert result["status"] == "updated"
    assert status_checker.cleared is True

    print("✓ Selected container updated")

    backup_path = Path(
        result["backup_path"]
    )

    assert backup_path.is_file()

    with zipfile.ZipFile(
        backup_path,
        mode="r",
    ) as archive:

        archived_files = set(
            archive.namelist()
        )

    assert "config/settings.json" in archived_files
    assert "compose/compose.yml" in archived_files
    assert "compose/.env" in archived_files

    print("✓ Configuration and environment backed up")

    assert any(
        command[-2:] == [
            "pull",
            "example",
        ]
        for command in commands
    )

    assert any(
        "up" in command
        and "--no-deps" in command
        and "--force-recreate" in command
        for command in commands
    )

    print("✓ Compose updated only the selected service")


with tempfile.TemporaryDirectory() as temporary:

    root = Path(temporary)
    compose_folder = root / "stack"
    config_folder = compose_folder / "app-data"

    config_folder.mkdir(parents=True)

    (
        config_folder / "settings.json"
    ).write_text(
        "{}",
        encoding="utf-8",
    )

    (
        compose_folder / "compose.yml"
    ).write_text(
        "services:\n  example:\n",
        encoding="utf-8",
    )

    definitions = {
        "example": {
            "name": "Example",
            "slug": "example",
            "container": "example",
            "service": "example",
            "image": "example/image:latest",
            "compose_folder": compose_folder,
            "config_folder": config_folder,
        }
    }

    commands = []
    state_checks = 0

    def rollback_runner(
        command,
        timeout,
        cwd=None,
    ):

        nonlocal_state = None
        commands.append(list(command))

        if (
            command[0:2]
            == ["docker", "inspect"]
            and "{{.Image}}" in command[-1]
        ):

            return (
                "sha256:"
                + ("d" * 64)
            )

        if (
            command[0:2]
            == ["docker", "inspect"]
            and "{{json .State}}" in command[-1]
        ):

            nonlocal_state = sum(
                1
                for recorded in commands
                if (
                    recorded[0:2]
                    == ["docker", "inspect"]
                    and "{{json .State}}"
                    in recorded[-1]
                )
            )

            if nonlocal_state == 1:

                return (
                    '{"Running": false, '
                    '"Status": "exited"}'
                )

            return (
                '{"Running": true, '
                '"Status": "running", '
                '"Health": {'
                '"Status": "healthy"}}'
            )

        if command[0:3] == [
            "docker",
            "image",
            "tag",
        ]:

            return ""

        if command[0:2] == [
            "docker",
            "compose",
        ]:

            return ""

        raise AssertionError(
            f"Unexpected command: {command}"
        )

    updater = ContainerUpdater(
        command_runner=rollback_runner,
        backup_root=root / "backups",
        containers=definitions,
    )

    result = updater.update("example")

    assert result["ok"] is False
    assert result["status"] == "failed"
    assert result["rollback_succeeded"] is True

    assert any(
        command[0:3] == [
            "docker",
            "image",
            "tag",
        ]
        for command in commands
    )

    print("✓ Previous image restored after failure")


unknown_result = updater.update(
    "not-allowed"
)

assert unknown_result["ok"] is False
assert unknown_result["status"] == "unknown"

print("✓ Unknown container rejected safely")

print()
print("✓ Controlled container update test passed")