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
            "spatial_control": "automatic",
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


class FakeOnboarding:

    def snapshot(
        self,
        profile,
        completed=False,
        playback_active=False,
    ):

        return {
            "profile": profile,
            "completed": completed,
            "display": {
                "available": True,
                "resolution": "3840x2160",
                "refresh": 120,
                "message": "3840x2160 at 120 Hz",
            },
            "audio": {
                "available": True,
                "name": "DENON-AVR HDMI",
                "form_factor": "HDMI/display audio",
                "message": "DENON-AVR HDMI",
            },
            "stremio": {
                "state": "ready",
                "ready": True,
                "message": "Playback detection is ready.",
            },
            "areas": [
                {
                    "id": "display",
                    "name": "Display",
                    "ready": True,
                    "detail": "3840x2160 at 120 Hz",
                },
                {
                    "id": "audio",
                    "name": "Audio output",
                    "ready": True,
                    "detail": "DENON-AVR HDMI",
                },
                {
                    "id": "playback",
                    "name": "Playback",
                    "ready": True,
                    "detail": "AIOStreams",
                },
                {
                    "id": "services",
                    "name": "Docker services",
                    "ready": True,
                    "detail": "1 configured",
                },
            ],
            "detected_count": 4,
            "area_count": 4,
            "discovered_services": [
                {
                    "id": "usenetstreamer-7001",
                    "name": "usenetstreamer",
                    "container": "usenetstreamer",
                    "image": "gavpyro/usenetstreamer:latest",
                    "port": 7001,
                    "url": "http://localhost:7001",
                    "recommended": True,
                }
            ],
            "discovery_errors": [],
            "detected_providers": ["AIOStreams"],
        }

    def merge_services(self, configured, candidate_ids):

        services = list(configured)

        if "usenetstreamer-7001" in candidate_ids:
            services.append(
                {
                    "name": "usenetstreamer",
                    "container": "usenetstreamer",
                    "port": 7001,
                    "url": "http://localhost:7001",
                }
            )

        return services


original_manager = routes.setup_profile_manager
original_display = routes.DisplayAdapter
original_reload = routes.service_status.reload
original_onboarding = routes.onboarding_assistant

manager = FakeProfileManager()
routes.setup_profile_manager = manager
routes.DisplayAdapter = FakeDisplay
routes.service_status.reload = lambda: None
routes.onboarding_assistant = FakeOnboarding()

try:
    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/setup")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "System Setup · Orion" in page
    assert "Set up Orion" in page
    assert "Detected for you" not in page
    assert "Current setup" in page
    assert "4/4 areas ready" in page
    assert "DENON-AVR HDMI" in page
    assert "Found on this computer" in page
    assert "usenetstreamer" in page
    assert "Recommended" in page
    candidate_control = page.split(
        'value="usenetstreamer-7001"',
        1,
    )[1].split(">", 1)[0]
    assert "checked" not in candidate_control
    assert "Living room display" in page
    assert "3840x2160" in page
    assert "120 Hz" in page
    assert "Automatic — derived from stream FPS" in page
    assert 'name="movie_refresh_rate"' not in page
    assert 'name="tv_refresh_rate"' not in page
    assert "AIOStreams" in page
    assert "Denon / Marantz" in page
    assert "192.168.1.50" in page
    assert 'name="spatial_control"' in page
    assert "Automatic — switch and restore with a checkpoint" in page
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
            "spatial_control": "automatic",
            "preferred_audio_format": "Atmos",
            "providers": [
                "AIOStreams",
                "UsenetStreamer",
            ],
            "discovered_services": [
                "usenetstreamer-7001",
            ],
        },
    )

    assert saved.status_code == 302
    assert manager.saved["services"][0] == PROFILE["services"][0]
    assert manager.saved["services"][1][
        "container"
    ] == "usenetstreamer"
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
    assert manager.saved["media"]["audio"][
        "spatial_control"
    ] == "automatic"

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
    routes.onboarding_assistant = original_onboarding

print()
print("✓ Orion setup page test passed")
