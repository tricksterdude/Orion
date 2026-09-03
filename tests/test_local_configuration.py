import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.local_configuration import LocalConfiguration


print("=" * 60)
print("LOCAL CONFIGURATION TEST")
print("=" * 60)
print()


with TemporaryDirectory() as directory:

    root = Path(directory)
    (root / "config").mkdir()
    (root / "data").mkdir()

    legacy_services = {
        "services": [
            {
                "name": "Example",
                "container": "example",
                "port": 8080,
                "url": "http://localhost:8080",
            }
        ]
    }
    legacy_providers = {
        "providers": ["AIOStreams"]
    }
    legacy_media = {
        "display": {
            "name": "Cinema display",
            "desktop_refresh_rate": 120,
            "movie_refresh_rate": 23.976,
            "tv_refresh_rate": 50,
            "hdr": True,
            "resolution": "3840x2160",
        },
        "audio": {
            "receiver": "AVR",
            "preferred_format": "Atmos",
        },
        "playback": {
            "player": "Stremio",
            "restore_desktop_after_playback": True,
        },
    }

    (root / "config" / "services.json").write_text(
        json.dumps(legacy_services),
        encoding="utf-8",
    )
    (root / "config" / "providers.json").write_text(
        json.dumps(legacy_providers),
        encoding="utf-8",
    )
    (root / "data" / "media_profile.json").write_text(
        json.dumps(legacy_media),
        encoding="utf-8",
    )

    configuration = LocalConfiguration(
        project_root=root
    )
    migrated = configuration.migrate_all()

    assert all(path.is_file() for path in migrated.values())
    assert configuration.read("services") == legacy_services
    assert configuration.read("providers") == legacy_providers
    assert configuration.read("media") == legacy_media

    print("✓ Existing installation copied into a local profile")

    changed = {"services": []}
    configuration.write("services", changed)

    assert configuration.read("services") == changed
    assert json.loads(
        (root / "config" / "services.json").read_text(
            encoding="utf-8"
        )
    ) == legacy_services

    print("✓ Local changes do not modify tracked defaults")

    configuration.write(
        "services",
        legacy_services,
    )
    configuration.prepare_public_defaults()

    assert configuration.read("services") == legacy_services
    assert json.loads(
        (root / "config" / "services.json").read_text(
            encoding="utf-8"
        )
    ) == {"services": []}
    assert json.loads(
        (root / "config" / "providers.json").read_text(
            encoding="utf-8"
        )
    ) == {"providers": []}
    assert json.loads(
        (root / "data" / "media_profile.json").read_text(
            encoding="utf-8"
        )
    )["display"]["desktop_refresh_rate"] == 60

    print("✓ Public defaults can be neutralised after migration")

with TemporaryDirectory() as directory:

    configuration = LocalConfiguration(
        project_root=directory
    )
    services = configuration.read("services")
    media = configuration.read("media")

    assert services == {"services": []}
    assert media["display"]["desktop_refresh_rate"] == 60
    assert "movie_refresh_rate" not in media["display"]
    assert "tv_refresh_rate" not in media["display"]
    assert configuration.local_path("media").is_file()

    print("✓ New installations receive neutral safe defaults")

print()
print("✓ Local configuration test passed")
