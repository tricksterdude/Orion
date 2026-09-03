import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.config_manager import ConfigManager
from app.metadata.tmdb_manager import TMDbManager
from app.secure_settings import (
    SecureSettingsError,
    SecureSettingsStore,
)


print("=" * 60)
print("SECURE SETTINGS TEST")
print("=" * 60)
print()


class TestProtector:

    def protect(self, value):

        return b"protected:" + value[::-1]

    def unprotect(self, value):

        if not value.startswith(b"protected:"):
            raise ValueError("invalid protected value")

        return value[len(b"protected:") :][::-1]


KEY = "0123456789abcdef0123456789abcdef"


with TemporaryDirectory() as directory:

    root = Path(directory)
    private_file = root / "secure_settings.json"
    store = SecureSettingsStore(
        path=private_file,
        protector=TestProtector(),
    )

    assert store.get(store.TMDB_API_KEY) is None
    assert not store.configured(store.TMDB_API_KEY)

    store.set(store.TMDB_API_KEY, KEY)

    assert store.get(store.TMDB_API_KEY) == KEY
    assert store.configured(store.TMDB_API_KEY)
    assert private_file.is_file()
    assert KEY not in private_file.read_text(
        encoding="utf-8"
    )

    payload = json.loads(
        private_file.read_text(encoding="utf-8")
    )
    assert payload["version"] == 1
    assert payload["protected_data"]

    print("✓ Private settings are encrypted and recoverable")

    try:
        store.set(store.TMDB_API_KEY, "not-a-key")
        raise AssertionError("Invalid key was accepted")
    except SecureSettingsError as error:
        assert "32-character" in str(error)

    assert store.get(store.TMDB_API_KEY) == KEY

    print("✓ Invalid TMDb keys are rejected without data loss")

    assert store.delete(store.TMDB_API_KEY)
    assert not private_file.exists()
    assert not store.delete(store.TMDB_API_KEY)

    print("✓ Private settings can be removed")

    private_file.write_text(
        "not valid json",
        encoding="utf-8",
    )

    try:
        store.get(store.TMDB_API_KEY)
        raise AssertionError("Corrupt data was accepted")
    except SecureSettingsError as error:
        assert "could not unlock" in str(error)

    print("✓ Corrupt private data fails closed")

with TemporaryDirectory() as directory:

    root = Path(directory)
    settings_file = root / "settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "application": "Orion",
                "author": "Test",
                "tmdb": {"api_key": KEY},
            }
        ),
        encoding="utf-8",
    )
    store = SecureSettingsStore(
        path=root / "secure.json",
        protector=TestProtector(),
    )

    config = ConfigManager(
        settings_file=settings_file,
        secure_settings=store,
    )

    assert config.get("tmdb.api_key") == KEY
    assert store.get(store.TMDB_API_KEY) == KEY

    print("✓ Legacy private settings migrate into secure storage")

tmdb = TMDbManager.__new__(TMDbManager)
tmdb.api_key = None
assert tmdb.lookup_imdb("tt0133093") is None

print("✓ Missing TMDb credentials skip remote lookup safely")

print()
print("✓ Secure settings test passed")
