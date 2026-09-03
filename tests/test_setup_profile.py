import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from app.local_configuration import LocalConfiguration
from app.setup_profile import (
    SetupProfileError,
    SetupProfileManager,
)


print("=" * 60)
print("SETUP PROFILE TEST")
print("=" * 60)
print()


PROFILE = {
    "version": 1,
    "media": {
        "display": {
            "name": "Cinema display",
            "desktop_refresh_rate": 120,
            "movie_refresh_rate": 23.976,
            "tv_refresh_rate": 50,
            "hdr": True,
            "resolution": "3840x2160",
        },
        "audio": {
            "receiver": "Living room AVR",
            "preferred_format": "Automatic",
        },
        "playback": {
            "player": "Stremio",
            "restore_desktop_after_playback": True,
        },
    },
    "services": [
        {
            "name": "AIOStreams",
            "container": "aiostreams",
            "port": 3500,
            "url": "http://localhost:3500",
        }
    ],
    "providers": ["AIOStreams"],
}


with TemporaryDirectory() as directory:

    root = Path(directory)
    configuration = LocalConfiguration(root)
    manager = SetupProfileManager(
        configuration=configuration,
        backup_root=root / "backups",
    )

    backup = manager.save(PROFILE)

    assert manager.completed()
    assert manager.snapshot() == PROFILE
    assert backup.is_file()

    with zipfile.ZipFile(backup) as archive:
        names = set(archive.namelist())
        assert "profile/media.json" in names
        assert "profile/services.json" in names
        assert "profile/providers.json" in names

    print("✓ Valid profile saved, verified and backed up")

    exported = manager.export_text()
    exported_data = json.loads(exported)

    assert exported_data == PROFILE
    assert "api_key" not in exported.casefold()
    assert "password" not in exported.casefold()

    print("✓ Export contains only the non-secret profile schema")

    imported = json.loads(exported)
    imported["media"]["display"]["name"] = "Imported display"
    imported["private"] = {"api_key": "must-not-be-used"}

    manager.import_bytes(
        json.dumps(imported).encode("utf-8")
    )

    assert manager.snapshot()["media"]["display"][
        "name"
    ] == "Imported display"
    assert "private" not in manager.snapshot()

    print("✓ Imported profiles are allow-listed and applied")

    original = manager.snapshot()
    invalid = json.loads(manager.export_text())
    invalid["services"].append(
        dict(invalid["services"][0])
    )

    try:
        manager.import_bytes(
            json.dumps(invalid).encode("utf-8")
        )
        raise AssertionError("Duplicate service was accepted")
    except SetupProfileError as error:
        assert "duplicate" in str(error).casefold()

    assert manager.snapshot() == original

    print("✓ Invalid imports cannot alter the current profile")

    oversized = b"{" + (
        b"x" * manager.MAX_IMPORT_BYTES
    )

    try:
        manager.import_bytes(oversized)
        raise AssertionError("Oversized profile was accepted")
    except SetupProfileError as error:
        assert "256 KB" in str(error)

    print("✓ Oversized profile imports are rejected")

print()
print("✓ Setup profile test passed")
