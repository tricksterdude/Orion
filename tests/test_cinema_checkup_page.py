from app.api import routes
from app.api.server import OrionAPIServer
from app.cinema_checkup import CinemaCheckupError


print("=" * 60)
print("CINEMA CHECKUP PAGE TEST")
print("=" * 60)
print()


SNAPSHOT = {
    "version": 1,
    "generated_at": "2026-09-05T12:00:00+00:00",
    "status": "warning",
    "label": "Ready with notes",
    "counts": {
        "healthy": 10,
        "warning": 1,
        "action_required": 0,
    },
    "checks": [
        {
            "id": "desktop_baseline",
            "category": "Picture",
            "name": "Desktop restoration baseline",
            "status": "healthy",
            "label": "Ready",
            "summary": "The desktop baseline is ready.",
            "guidance": "No action is required.",
            "detail": "3840x2160 at 120 Hz.",
        },
        {
            "id": "playback_evidence",
            "category": "Proof",
            "name": "Recent playback recovery",
            "status": "warning",
            "label": "Ready with notes",
            "summary": "Complete one playback proof.",
            "guidance": "Play and stop one title.",
            "detail": None,
        },
    ],
}


class FakeCheckup:

    def __init__(self):

        self.calls = []

    def latest(self):

        return SNAPSHOT

    def run(self, services=None, playback_active=False):

        self.calls.append(
            {
                "services": services,
                "playback_active": playback_active,
            }
        )

        if playback_active:
            raise CinemaCheckupError(
                "Cinema Checkup cannot run during playback."
            )

        return SNAPSHOT


class FakeAudioGuidance:

    def __init__(self):

        self.active = False

    def get(self):

        return {"active": self.active}


original_checkup = routes.cinema_checkup
original_audio_guidance = routes.audio_guidance_status
original_service_get_all = routes.service_status.get_all

try:

    fake_checkup = FakeCheckup()
    fake_audio_guidance = FakeAudioGuidance()
    services = [{"name": "AIOStreams", "healthy": True}]
    routes.cinema_checkup = fake_checkup
    routes.audio_guidance_status = fake_audio_guidance
    routes.service_status.get_all = lambda: services

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/checkup")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Cinema Checkup · Orion" in page
    assert "One-button preflight" in page
    assert "Safe, read-only preflight" in page
    assert "Run Cinema Checkup" in page
    assert 'action="/checkup/run"' in page
    assert routes.cinema_checkup_token in page
    assert "Ready with notes" in page
    assert "Desktop restoration baseline" in page
    assert "Recent playback recovery" in page
    assert "Play and stop one title." in page
    assert response.headers["Cache-Control"] == "no-store, max-age=0"

    print("✓ Cinema Checkup page shows the latest clear, local result")

    denied = client.post("/checkup/run", data={})

    assert denied.status_code == 403

    print("✓ Checkup action rejects a missing security token")

    run_response = client.post(
        "/checkup/run",
        data={"token": routes.cinema_checkup_token},
    )

    assert run_response.status_code == 302
    assert "checkup_status=current" in run_response.location
    assert fake_checkup.calls[-1] == {
        "services": services,
        "playback_active": False,
    }

    print("✓ Protected checkup refresh receives current service status")

    fake_audio_guidance.active = True
    active_response = client.get("/checkup")
    active_page = active_response.get_data(as_text=True)

    assert active_response.status_code == 200
    assert "Stop the current title" in active_page
    assert "disabled" in active_page

    refused = client.post(
        "/checkup/run",
        data={"token": routes.cinema_checkup_token},
    )

    assert refused.status_code == 302
    assert "checkup_status=failed" in refused.location
    assert fake_checkup.calls[-1]["playback_active"] is True

    print("✓ Page and server both refuse a checkup during playback")

finally:

    routes.cinema_checkup = original_checkup
    routes.audio_guidance_status = original_audio_guidance
    routes.service_status.get_all = original_service_get_all

print()
print("✓ Cinema Checkup page test passed")
