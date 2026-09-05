from types import SimpleNamespace

from app.audio.guidance_status import AudioGuidanceStatus
from app.audio.windows_settings import WindowsSoundSettings


print("=" * 60)
print("LIVE AUDIO GUIDANCE TEST")
print("=" * 60)
print()


request = SimpleNamespace(
    title="Atmos Test",
    audio_codec="Dolby TrueHD",
    audio_profile="Dolby TrueHD + Dolby Atmos",
    immersive_audio="Dolby Atmos",
)

status = AudioGuidanceStatus()

checking = status.update(
    request,
    audio_output={"name": "DENON-AVR HDMI"},
    processing={
        "processor": "Dolby Access",
        "installed": True,
    },
    receiver={
        "available": True,
        "name": "Denon / Marantz",
        "sound_mode": "STEREO",
        "selected_input": "AUX1",
        "matches_expected_audio": False,
        "match_quality": "mismatch",
    },
    settled=False,
)

assert checking["active"] is True
assert checking["state"] == "checking"
assert checking["processor"] == "Dolby Access"

mismatch = status.update(
    request,
    audio_output={"name": "DENON-AVR HDMI"},
    processing={
        "processor": "Dolby Access",
        "installed": True,
    },
    receiver={
        "available": True,
        "name": "Denon / Marantz",
        "sound_mode": "DTS:X MSTR",
        "selected_input": "AUX1",
        "matches_expected_audio": False,
        "match_quality": "mismatch",
    },
    settled=True,
)

assert mismatch["state"] == "mismatch"
assert mismatch["expected_audio"] == "Dolby Atmos"
assert mismatch["receiver_mode"] == "DTS:X MSTR"
assert mismatch["matches"] is False

matched = status.update(
    request,
    receiver={
        "available": True,
        "name": "Denon / Marantz",
        "sound_mode": "DOLBY ATMOS",
        "matches_expected_audio": True,
        "match_quality": "exact",
    },
    settled=True,
)

assert matched["state"] == "matched"
assert matched["matches"] is True

compatible = status.update(
    request,
    receiver={
        "available": True,
        "name": "Denon / Marantz",
        "sound_mode": "DOLBY AUDIO-DSUR",
        "matches_expected_audio": True,
        "match_quality": "compatible",
    },
    settled=True,
)

assert compatible["state"] == "compatible"
assert compatible["match_quality"] == "compatible"

recovery_failed = status.recovery_failed()
assert recovery_failed["active"] is True
assert recovery_failed["state"] == "recovery_failed"
assert recovery_failed["automatic"] is True

status.clear()
assert status.get()["active"] is False

print("✓ Checking, mismatch and matched states published safely")


opened = []

settings = WindowsSoundSettings(
    launcher=opened.append,
    platform_name="nt",
)

result = settings.open()

assert result["ok"] is True
assert opened == ["ms-settings:sound"]

unsupported = WindowsSoundSettings(
    launcher=opened.append,
    platform_name="posix",
).open()

assert unsupported["ok"] is False


def failed_launcher(uri):

    raise OSError("unavailable")


failed = WindowsSoundSettings(
    launcher=failed_launcher,
    platform_name="nt",
).open()

assert failed["ok"] is False

print("✓ Official Windows sound-settings URI opens and fails safely")
print()
print("✓ Live audio guidance test passed")
