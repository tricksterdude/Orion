import json
import tempfile
import zipfile
from pathlib import Path

from app.api.service_registry import (
    ServiceRegistry,
)


print("=" * 60)
print("SERVICE REGISTRY TEST")
print("=" * 60)
print()


def write_services(path, services):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "services": services,
            },
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )


with tempfile.TemporaryDirectory() as directory:

    root = Path(directory)

    services_path = (
        root
        / "config"
        / "services.json"
    )

    backup_root = (
        root
        / "backups"
    )

    original_service = {
        "name": "AIOStreams",
        "container": "aiostreams",
        "port": 3500,
        "url": "http://localhost:3500",
    }

    write_services(
        services_path,
        [
            original_service,
        ],
    )

    registry = ServiceRegistry(
        services_config=services_path,
        backup_root=backup_root,
    )

    candidate = {
        "id": "example-service-8088",
        "name": "example-service",
        "container": "example-service",
        "image": "example/service:latest",
        "port": 8088,
        "url": "http://localhost:8088",
        "running": True,
        "status": "running",
        "health": "healthy",
    }

    result = registry.add(
        candidate,
        display_name="Example Service",
    )

    assert result["status"] == "added"
    assert result["service"] == {
        "name": "Example Service",
        "container": "example-service",
        "port": 8088,
        "url": "http://localhost:8088",
    }

    saved_document = json.loads(
        services_path.read_text(
            encoding="utf-8"
        )
    )

    assert len(
        saved_document["services"]
    ) == 2

    assert (
        saved_document["services"][0]
        == original_service
    )

    assert (
        saved_document["services"][1]
        == result["service"]
    )

    print("✓ Existing Docker service registered")

    backup_path = Path(
        result["backup"]
    )

    assert backup_path.exists()

    with zipfile.ZipFile(
        backup_path
    ) as archive:

        assert (
            "orion/services.json"
            in archive.namelist()
        )

        backed_up_document = json.loads(
            archive.read(
                "orion/services.json"
            ).decode("utf-8")
        )

    assert backed_up_document == {
        "services": [
            original_service,
        ],
    }

    print("✓ Service configuration backed up")

    duplicate_result = registry.add(
        candidate,
        display_name="Example Service",
    )

    assert (
        duplicate_result["status"]
        == "exists"
    )

    unchanged_document = json.loads(
        services_path.read_text(
            encoding="utf-8"
        )
    )

    assert unchanged_document == saved_document

    print("✓ Duplicate service rejected safely")

    duplicate_name_candidate = {
        **candidate,
        "container": "another-container",
        "port": 9091,
    }

    duplicate_name_result = registry.add(
        duplicate_name_candidate,
        display_name="Example Service",
    )

    assert (
        duplicate_name_result["status"]
        == "exists"
    )

    print("✓ Duplicate display name rejected safely")

    route_collision_result = registry.add(
        {
            **candidate,
            "container": "route-collision-service",
            "port": 9093,
        },
        display_name="ExampleService",
    )

    assert (
        route_collision_result["status"]
        == "exists"
    )

    print("✓ Service-page name collision rejected safely")

    invalid_name_result = registry.add(
        candidate,
        display_name="   ",
    )

    assert (
        invalid_name_result["status"]
        == "invalid"
    )

    invalid_port_result = registry.add(
        {
            **candidate,
            "container": "invalid-port-service",
            "port": 70000,
        },
        display_name="Invalid Port Service",
    )

    assert (
        invalid_port_result["status"]
        == "invalid"
    )

    invalid_container_result = registry.add(
        {
            **candidate,
            "container": "../unsafe",
            "port": 9092,
        },
        display_name="Unsafe Service",
    )

    assert (
        invalid_container_result["status"]
        == "invalid"
    )

    print("✓ Invalid service details rejected safely")


with tempfile.TemporaryDirectory() as directory:

    root = Path(directory)

    services_path = (
        root
        / "config"
        / "services.json"
    )

    backup_root = (
        root
        / "backups"
    )

    original_document = {
        "services": [
            {
                "name": "NZBDAV",
                "container": "nzbdav",
                "port": 8500,
                "url": "http://localhost:8500",
            }
        ],
    }

    original_text = (
        json.dumps(
            original_document,
            indent=4,
        )
        + "\n"
    )

    services_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    services_path.write_text(
        original_text,
        encoding="utf-8",
    )

    registry = ServiceRegistry(
        services_config=services_path,
        backup_root=backup_root,
    )

    real_write_atomic = (
        registry._write_atomic
    )

    write_attempts = {
        "count": 0,
    }

    def failing_first_write(
        path,
        text,
    ):

        write_attempts["count"] += 1

        if write_attempts["count"] == 1:

            raise OSError(
                "Simulated write failure"
            )

        return real_write_atomic(
            path,
            text,
        )

    registry._write_atomic = (
        failing_first_write
    )

    failed_result = registry.add(
        {
            "name": "Candidate",
            "container": "candidate",
            "port": 8080,
        },
        display_name="Candidate",
    )

    assert (
        failed_result["status"]
        == "failed"
    )

    assert (
        services_path.read_text(
            encoding="utf-8"
        )
        == original_text
    )

    restored_document = json.loads(
        services_path.read_text(
            encoding="utf-8"
        )
    )

    assert restored_document == (
        original_document
    )

    print("✓ Original configuration restored after failure")


print()
print("✓ Service registry test passed")
