from app.api import routes
from app.api.server import OrionAPIServer
from app.secure_settings import (
    SecureSettingsError,
    SecureSettingsStore,
)


print("=" * 60)
print("ORION SETTINGS PAGE TEST")
print("=" * 60)
print()


class TestSecureSettings:

    def __init__(self):

        self.value = None
        self.fail = False

    def get(self, key, default=None):

        if self.fail:
            raise SecureSettingsError(
                "Private settings are unavailable."
            )

        return self.value or default

    def configured(self, key):

        return bool(self.get(key))

    def set(self, key, value):

        self.value = SecureSettingsStore.validate(
            key,
            value,
        )

    def delete(self, key):

        existed = self.value is not None
        self.value = None
        return existed


original_store = routes.secure_settings_store
store = TestSecureSettings()
routes.secure_settings_store = store

try:
    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/settings")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Settings · Orion" in page
    assert "TMDb metadata" in page
    assert "Not configured" in page
    assert 'type="password"' in page
    assert routes.settings_management_token in page
    assert "no-store" in response.headers["Cache-Control"]

    print("✓ Settings page renders without exposing a key")

    missing_token = client.post(
        "/settings/tmdb",
        data={"action": "save", "api_key": "0" * 32},
    )
    assert missing_token.status_code == 403

    invalid = client.post(
        "/settings/tmdb",
        data={
            "token": routes.settings_management_token,
            "action": "save",
            "api_key": "invalid",
        },
        follow_redirects=True,
    )
    assert invalid.status_code == 200
    assert "32-character" in invalid.get_data(
        as_text=True
    )

    print("✓ Settings changes require a token and validation")

    key = "a" * 32
    saved = client.post(
        "/settings/tmdb",
        data={
            "token": routes.settings_management_token,
            "action": "save",
            "api_key": key,
        },
        follow_redirects=True,
    )
    saved_page = saved.get_data(as_text=True)

    assert saved.status_code == 200
    assert store.value == key
    assert "Configured" in saved_page
    assert "encrypted and saved" in saved_page
    assert key not in saved_page

    print("✓ TMDb key can be saved without being echoed")

    removed = client.post(
        "/settings/tmdb",
        data={
            "token": routes.settings_management_token,
            "action": "remove",
        },
        follow_redirects=True,
    )
    assert removed.status_code == 200
    assert store.value is None
    assert "was removed" in removed.get_data(
        as_text=True
    )

    print("✓ Saved TMDb key can be removed")

    store.fail = True
    unavailable = client.get("/settings")
    unavailable_page = unavailable.get_data(
        as_text=True
    )
    assert unavailable.status_code == 200
    assert "Needs attention" in unavailable_page
    assert "Private settings are unavailable" in unavailable_page

    print("✓ Secure-storage failures are harmless and visible")

finally:
    routes.secure_settings_store = original_store

print()
print("✓ Orion settings page test passed")
