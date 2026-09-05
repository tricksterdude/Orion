import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from app.cinema_checkup import CinemaCheckup, CinemaCheckupError


print("=" * 60)
print("CINEMA CHECKUP TEST")
print("=" * 60)
print()


PROFILE = {
    "version": 1,
    "media": {
        "display": {
            "name": "Cinema display",
            "resolution": "3840x2160",
            "desktop_refresh_rate": 120,
            "hdr": True,
        },
        "audio": {
            "receiver": "Living room AVR",
            "preferred_format": "Automatic",
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


class FakeDiagnostics:

    def __init__(self):

        self.calls = []

    def run(self, services=None, force=False):

        self.calls.append(
            {
                "services": services,
                "force": force,
            }
        )

        identifiers = (
            "configuration",
            "docker",
            "ffprobe",
            "display",
            "audio_output",
            "single_instance",
            "stremio",
            "services",
        )

        return {
            "checks": [
                {
                    "id": identifier,
                    "name": identifier.replace("_", " ").title(),
                    "status": "healthy",
                    "label": "Healthy",
                    "summary": "The check passed.",
                    "guidance": "No action is required.",
                    "detail": None,
                }
                for identifier in identifiers
            ]
        }


class FakeProfile:

    def __init__(self):

        self.is_completed = True

    def snapshot(self):

        return json.loads(json.dumps(PROFILE))

    def completed(self):

        return self.is_completed


class FakeDisplay:

    def __init__(self):

        self.mode = SimpleNamespace(
            width=3840,
            height=2160,
            refresh=120,
        )

    def current_mode(self):

        return self.mode


class FakeDisplayRecovery:

    def __init__(self):

        self.pending = False

    def has_saved_mode(self):

        return self.pending


class FakeSpatialAudio:

    def __init__(self):

        self.result = {
            "mode": "automatic",
            "helpers_available": True,
            "checkpoint_pending": False,
        }

    def status(self):

        return dict(self.result)


class FakeHistory:

    def __init__(self):

        self.sessions = [
            {
                "playback": {
                    "source": "AIOStreams",
                    "fps": 23.976,
                    "audio_profile": (
                        "Dolby TrueHD + Dolby Atmos"
                    ),
                },
                "display_restored": True,
                "audio_restored": True,
            }
        ]

    def read(self, limit=100):

        return self.sessions[:limit]


def find_check(snapshot, identifier):

    return next(
        check
        for check in snapshot["checks"]
        if check["id"] == identifier
    )


with TemporaryDirectory() as directory:

    diagnostics = FakeDiagnostics()
    profile = FakeProfile()
    display = FakeDisplay()
    display_recovery = FakeDisplayRecovery()
    spatial_audio = FakeSpatialAudio()
    history = FakeHistory()
    path = Path(directory) / "cinema_checkup.json"
    checkup = CinemaCheckup(
        diagnostics=diagnostics,
        setup_profile=profile,
        display=display,
        display_recovery=display_recovery,
        spatial_audio=spatial_audio,
        history=history,
        path=path,
    )
    services = [{"name": "AIOStreams"}]

    result = checkup.run(services=services)

    assert result["status"] == "healthy"
    assert result["label"] == "Ready"
    assert result["counts"]["healthy"] == 12
    assert diagnostics.calls == [
        {
            "services": services,
            "force": True,
        }
    ]
    assert path.is_file()
    assert checkup.latest() == result
    assert find_check(result, "docker")["category"] == "Foundation"
    assert find_check(result, "audio_output")["category"] == "Audio"
    assert find_check(result, "docker")["label"] == "Ready"

    print("✓ Complete cinema path produces a saved Ready result")
    print("✓ Existing diagnostics are refreshed and grouped clearly")

    saved = path.read_text(encoding="utf-8")

    try:
        checkup.run(
            services=services,
            playback_active=True,
        )
        raise AssertionError(
            "Active playback should block Cinema Checkup"
        )
    except CinemaCheckupError as error:
        assert "cannot run during playback" in str(error)

    assert path.read_text(encoding="utf-8") == saved

    print("✓ Active playback is refused without replacing the last result")

    display.mode = SimpleNamespace(
        width=3840,
        height=2160,
        refresh=23,
    )
    result = checkup.run()

    assert result["status"] == "warning"
    assert (
        find_check(result, "desktop_baseline")["status"]
        == "warning"
    )

    print("✓ Temporary cinema refresh is not mistaken for the desktop baseline")

    display.mode = SimpleNamespace(
        width=3840,
        height=2160,
        refresh=120,
    )
    display_recovery.pending = True
    result = checkup.run()

    assert result["status"] == "action_required"
    assert find_check(result, "recovery")["status"] == "action_required"

    print("✓ Unfinished recovery checkpoints require attention")

    display_recovery.pending = False
    history.sessions = []
    result = checkup.run()

    assert result["status"] == "warning"
    assert (
        find_check(result, "playback_evidence")["status"]
        == "warning"
    )

    history.sessions = [
        {
            "playback": {"source": "AIOStreams"},
            "display_restored": False,
            "audio_restored": True,
        }
    ]
    result = checkup.run()

    assert result["status"] == "action_required"
    assert (
        find_check(result, "playback_evidence")["status"]
        == "action_required"
    )

    print("✓ Missing and failed playback recovery evidence is explained")

    path.write_text("not-json", encoding="utf-8")
    assert checkup.latest() is None

    print("✓ Corrupt saved results fail closed")

print()
print("✓ Cinema Checkup test passed")
