import io
import json

from app.api import routes
from app.api.server import OrionAPIServer
from app.setup_profile import SetupProfileError


print("=" * 60)
print("ORION SETUP PAGE TEST")
print("=" * 60)
print()


PROFILE = {
    "version": 1,
    "media": {
        "display": {
            "name": "Living room display",
            "desktop_refresh_rate": 120,
            "hdr": True,
            "resolution": "3840x2160",
        },
        "audio": {
            "receiver": "Living room AVR",
            "preferred_format": "Dolby Atmos",
            "receiver_adapter": "denon_marantz",
            "receiver_host": "192.168.1.50",
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


class FakeProfileManager:

    VERSION = 1
    MAX_IMPORT_BYTES = 256 * 1024
    SUPPORTED_PROVIDERS = (
        "AIOStreams",
        "UsenetStreamer",
    )

    def __init__(self):

        self.profile = json.loads(json.dumps(PROFILE))
        self.saved = None
        self.imported = None

    def snapshot(self):

        return self.profile

    def completed(self):

        return True

    def save(self, profile):

        self.saved = profile

    def export_text(self):

        return json.dumps(self.profile)

    def import_bytes(self, content):

        if content == b"invalid":
            raise SetupProfileError(
                "The selected file is not a valid Orion profile."
            )

        self.imported = content


class FakeMode:

    width = 3840
    height = 2160
    refresh = 120


class FakeDisplay:

    def current_mode(self):

        return FakeMode()


original_manager = routes.setup_profile_manager
original_display = routes.DisplayAdapter
original_reload = routes.service_status.reload

manager = FakeProfileManager()
routes.setup_profile_manager = manager
routes.DisplayAdapter = FakeDisplay
routes.service_status.reload = lambda: None

try:
    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/setup")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "System Setup · Orion" in page
    assert "Living room display" in page
    assert "3840x2160" in page
    assert "120 Hz" in page
    assert "Automatic — derived from stream FPS" in page
    assert 'name="movie_refresh_rate"' not in page
    assert 'name="tv_refresh_rate"' not in page
    assert "AIOStreams" in page
    assert "Denon / Marantz" in page
    assert "192.168.1.50" in page
    assert routes.settings_management_token in page
    assert "no-store" in response.headers["Cache-Control"]

    print("✓ Setup page shows current and detected configuration")

    denied = client.post("/setup/save", data={})
    assert denied.status_code == 403

    saved = client.post(
        "/setup/save",
        data={
            "token": routes.settings_management_token,
            "display_name": "Cinema display",
            "resolution": "3840x2160",
            "desktop_refresh_rate": "120",
            "hdr": "on",
            "restore_desktop": "on",
            "player": "Stremio",
            "receiver": "AVR",
            "receiver_adapter": "denon_marantz",
            "receiver_host": "192.168.1.60",
            "preferred_audio_format": "Atmos",
            "providers": [
                "AIOStreams",
                "UsenetStreamer",
            ],
        },
    )

    assert saved.status_code == 302
    assert manager.saved["services"] == PROFILE["services"]
    assert manager.saved["providers"] == [
        "AIOStreams",
        "UsenetStreamer",
    ]
    assert manager.saved["media"]["display"][
        "desktop_refresh_rate"
    ] == "120"
    assert manager.saved["media"]["audio"][
        "preferred_format"
    ] == "Automatic"
    assert manager.saved["media"]["audio"][
        "receiver_adapter"
    ] == "denon_marantz"
    assert manager.saved["media"]["audio"][
        "receiver_host"
    ] == "192.168.1.60"

    print("✓ Setup changes require a token and preserve services")

    export_denied = client.post(
        "/settings/profile/export"
    )
    assert export_denied.status_code == 403

    exported = client.post(
        "/settings/profile/export",
        data={"token": routes.settings_management_token},
    )

    assert exported.status_code == 200
    assert exported.mimetype == "application/json"
    assert (
        "orion-profile.json"
        in exported.headers["Content-Disposition"]
    )
    assert "no-store" in exported.headers["Cache-Control"]

    print("✓ Profile export is secured and non-cacheable")

    imported = client.post(
        "/settings/profile/import",
        data={
            "token": routes.settings_management_token,
            "profile": (
                io.BytesIO(b'{"version": 1}'),
                "orion-profile.json",
            ),
        },
        content_type="multipart/form-data",
    )

    assert imported.status_code == 302
    assert manager.imported == b'{"version": 1}'

    invalid = client.post(
        "/settings/profile/import",
        data={
            "token": routes.settings_management_token,
            "profile": (
                io.BytesIO(b"invalid"),
                "invalid.json",
            ),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert invalid.status_code == 200
    assert "not a valid Orion profile" in invalid.get_data(
        as_text=True
    )

    print("✓ Profile imports are secured and errors are explained")

finally:
    routes.setup_profile_manager = original_manager
    routes.DisplayAdapter = original_display
    routes.service_status.reload = original_reload

print()
print("✓ Orion setup page test passed")
