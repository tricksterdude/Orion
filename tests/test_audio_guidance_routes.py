from types import SimpleNamespace

from app.api import routes
from app.api.server import OrionAPIServer
from app.audio.guidance_status import audio_guidance_status


print("=" * 60)
print("LIVE AUDIO GUIDANCE ROUTE TEST")
print("=" * 60)
print()


class FakeWindowsSoundSettings:

    def __init__(self):

        self.opens = 0

    def open(self):

        self.opens += 1

        return {
            "ok": True,
            "message": "Windows sound settings opened.",
        }


original_settings = routes.windows_sound_settings
fake_settings = FakeWindowsSoundSettings()

try:

    routes.windows_sound_settings = fake_settings

    audio_guidance_status.update(
        SimpleNamespace(
            title="Atmos Test",
            audio_codec="Dolby TrueHD",
            audio_profile="Dolby TrueHD + Dolby Atmos",
            immersive_audio="Dolby Atmos",
        ),
        audio_output={"name": "DENON-AVR HDMI"},
        processing={
            "processor": "Dolby Access",
            "installed": True,
        },
        receiver={
            "available": True,
            "name": "Denon / Marantz",
            "sound_mode": "DTS:X MSTR",
            "matches_expected_audio": False,
        },
        settled=True,
    )

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/audio-guidance/status")
    document = response.get_json()

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert document["state"] == "mismatch"
    assert document["receiver_mode"] == "DTS:X MSTR"

    denied = client.post(
        "/audio-guidance/open-settings",
        data={"token": "wrong"},
    )

    assert denied.status_code == 403
    assert fake_settings.opens == 0

    opened = client.post(
        "/audio-guidance/open-settings",
        data={
            "token": routes.audio_guidance_token,
        },
    )

    assert opened.status_code == 302
    assert fake_settings.opens == 1
    assert "update_status=updated" in opened.location

    print("✓ Live status is current and non-cacheable")
    print("✓ Windows settings action requires Orion's token")

finally:

    routes.windows_sound_settings = original_settings
    audio_guidance_status.clear()

print()
print("✓ Live audio guidance route test passed")
