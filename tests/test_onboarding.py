from types import SimpleNamespace

from app.onboarding import OnboardingAssistant, OnboardingError


print("=" * 60)
print("STREAMLINED ONBOARDING TEST")
print("=" * 60)
print()


PROFILE = {
    "version": 1,
    "media": {
        "display": {
            "name": "Primary display",
            "desktop_refresh_rate": 60,
            "hdr": False,
            "resolution": "1920x1080",
        },
        "audio": {
            "receiver": "Not configured",
            "preferred_format": "Automatic",
            "receiver_adapter": "none",
            "receiver_host": "",
            "spatial_control": "guided",
        },
        "playback": {
            "player": "Stremio",
            "restore_desktop_after_playback": True,
        },
    },
    "services": [],
    "providers": [],
}


class Display:

    def current_mode(self):

        return SimpleNamespace(
            width=3840,
            height=2160,
            refresh=120,
        )


class Audio:

    def default_endpoint(self):

        return SimpleNamespace(
            name="DENON-AVR (HDMI)",
            active=True,
            form_factor="HDMI/display audio",
        )


class Stremio:

    def status(self):

        return {
            "state": "stopped",
            "ready": False,
            "can_launch": True,
            "message": "Stremio is installed.",
        }


class Discovery:

    CANDIDATES = [
        {
            "id": "aiostreams-3500",
            "name": "aiostreams",
            "container": "aiostreams",
            "image": "ghcr.io/viren070/aiostreams:latest",
            "port": 3500,
            "url": "http://localhost:3500",
            "running": True,
            "status": "running",
            "health": "healthy",
        },
        {
            "id": "example-8080",
            "name": "example",
            "container": "example",
            "image": "example/service:latest",
            "port": 8080,
            "url": "http://localhost:8080",
            "running": True,
            "status": "running",
            "health": None,
        },
    ]

    def discover(self, configured_services=None):

        configured = {
            (
                service["container"].casefold(),
                service["port"],
            )
            for service in configured_services or []
        }

        return {
            "candidates": [
                dict(candidate)
                for candidate in self.CANDIDATES
                if (
                    candidate["container"].casefold(),
                    candidate["port"],
                ) not in configured
            ],
            "errors": [],
        }


assistant = OnboardingAssistant(
    display=Display(),
    audio_output=Audio(),
    stremio=Stremio(),
    service_discovery=Discovery(),
)

snapshot = assistant.snapshot(PROFILE, completed=False)

assert snapshot["detected_count"] == 4
assert snapshot["area_count"] == 4
assert snapshot["profile"]["media"]["display"][
    "resolution"
] == "3840x2160"
assert snapshot["profile"]["media"]["display"][
    "desktop_refresh_rate"
] == 120
assert snapshot["profile"]["media"]["audio"][
    "receiver"
] == "DENON-AVR (HDMI)"
assert snapshot["profile"]["providers"] == [
    "AIOStreams"
]
assert snapshot["discovered_services"][0][
    "recommended"
] is True
assert snapshot["discovered_services"][1][
    "recommended"
] is False

print("✓ Display, audio, playback and Docker choices detected")
print("✓ Safe first-run values pre-filled")
print("✓ Known cinema services recommended")

completed = assistant.snapshot(PROFILE, completed=True)

assert completed["profile"]["media"]["display"][
    "resolution"
] == "1920x1080"
assert completed["profile"]["media"]["audio"][
    "receiver"
] == "Not configured"
assert completed["profile"]["providers"] == []

print("✓ Completed profiles are never overwritten by detection")

playing = assistant.snapshot(
    PROFILE,
    completed=False,
    playback_active=True,
)

assert playing["profile"]["media"]["display"][
    "desktop_refresh_rate"
] == 60
assert "baseline preserved" in playing["display"]["message"]

print("✓ Active playback cannot become the desktop baseline")

merged = assistant.merge_services(
    [],
    ["aiostreams-3500", "example-8080"],
)

assert len(merged) == 2
assert merged[0]["name"] == "aiostreams"
assert merged[1]["name"] == "example"

duplicate_name = assistant.merge_services(
    [
        {
            "name": "aiostreams",
            "container": "other",
            "port": 9000,
            "url": "http://localhost:9000",
        }
    ],
    ["aiostreams-3500"],
)

assert duplicate_name[-1]["name"] == "aiostreams 3500"

print("✓ Selected services merge without display-name collisions")

try:
    assistant.merge_services([], ["fabricated-9999"])
    raise AssertionError("A fabricated Docker candidate was accepted")
except OnboardingError as error:
    assert "no longer available" in str(error)

print("✓ Stale or fabricated Docker choices are rejected")


class Unavailable:

    def current_mode(self):

        raise RuntimeError("Unavailable")

    def default_endpoint(self):

        raise RuntimeError("Unavailable")

    def status(self):

        raise RuntimeError("Unavailable")

    def discover(self, configured_services=None):

        raise RuntimeError("Unavailable")


unavailable = OnboardingAssistant(
    display=Unavailable(),
    audio_output=Unavailable(),
    stremio=Unavailable(),
    service_discovery=Unavailable(),
).snapshot(PROFILE, completed=False)

assert unavailable["detected_count"] == 0
assert unavailable["profile"] == PROFILE
assert unavailable["discovery_errors"]

print("✓ Optional detection failures remain harmless")
print()
print("✓ Streamlined onboarding test passed")
