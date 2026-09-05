from pathlib import Path
from tempfile import TemporaryDirectory

from app.api import routes
from app.api.server import OrionAPIServer
from app.playback.history import PlaybackHistory


print("=" * 60)
print("PLAYBACK HISTORY PAGE TEST")
print("=" * 60)
print()

original_history_store = (
    routes.history_store
)
original_history_token = (
    routes.history_management_token
)

try:

    with TemporaryDirectory() as directory:

        history_path = (
            Path(directory)
            / "playback_history.jsonl"
        )

        test_history = PlaybackHistory(
            history_path
        )

        session = {
            "session_id": "page-test",
            "started_at": (
                "2026-08-17T19:00:00+00:00"
            ),
            "ended_at": (
                "2026-08-17T19:02:00+00:00"
            ),
            "duration_seconds": 120,
            "playback": {
                "title": None,
                "filename": (
                    "The.Matrix.1999.2160p."
                    "BluRay.HEVC.mkv"
                ),
                "resolution": "3840x2160",
                "fps": 23.976,
                "hdr": True,
                "dolby_vision": False,
                "video_codec": "hevc",
                "audio_codec": "Dolby TrueHD",
                "audio_channels": "7.1",
                "audio_sample_rate": 48000,
                "audio_bitrate": 4000000,
                "immersive_audio": "Dolby Atmos",
                "source": "UsenetStreamer",
            },
            "audio_output": {
                "name": "DENON-AVR HDMI",
                "active": True,
                "form_factor": "HDMI/display audio",
            },
            "audio_processing": {
                "policy": "Automatic",
                "processor": "Dolby Access",
                "installed": True,
                "control": "observe_only",
            },
            "receiver": {
                "adapter": "denon_marantz",
                "name": "Denon / Marantz",
                "available": True,
                "sound_mode": "DOLBY ATMOS",
                "selected_input": "GAME",
                "expected_immersive_audio": "Dolby Atmos",
                "matches_expected_audio": True,
                "match_quality": "exact",
            },
            "audio_control": {
                "status": "switched",
                "changed": True,
            },
            "audio_restored": True,
            "cinema": {
                "current_mode": {
                    "refresh": 120,
                },
                "target_mode": {
                    "refresh": 23,
                },
                "switched": True,
            },
            "display_restored": True,
        }

        assert test_history._append(
            session
        )

        legacy_session = dict(session)
        legacy_session["session_id"] = "legacy-page-test"
        legacy_session.pop("audio_control")
        legacy_session.pop("audio_restored")

        assert test_history._append(
            legacy_session
        )

        routes.history_store = (
            test_history
        )

        page_token = routes.history_management_token

        server = OrionAPIServer()
        client = server.app.test_client()

        response = client.get(
            "/history/view"
        )

        assert response.status_code == 200

        page = response.get_data(
            as_text=True
        )

        assert "Playback History" in page
        assert "The Matrix (1999)" in page
        assert "UsenetStreamer" in page
        assert "23.976 fps" in page
        assert "Dolby TrueHD" in page
        assert "Dolby Atmos" in page
        assert "7.1" in page
        assert "48.0 kHz" in page
        assert "4000 kbps" in page
        assert "DENON-AVR HDMI" in page
        assert "Dolby Access" in page
        assert "Denon / Marantz" in page
        assert "DOLBY ATMOS" in page
        assert "Exact immersive mode" in page
        assert "Spatial format switched automatically" in page
        assert "Previous spatial format restored" in page
        assert "available" in page
        assert "Display restored" in page
        assert 'href="/"' in page
        assert "Back to Orion" in page
        assert "Delete all" in page
        assert (
            'action="/history/page-test/delete"'
            in page
        )
        assert page_token in page
        assert "no-store" in response.headers["Cache-Control"]

        print(
            "✓ Playback history page rendered"
        )
        print(
            "✓ Friendly title generated"
        )
        print(
            "✓ Session details displayed"
        )
        print(
            "✓ Display status displayed"
        )
        print(
            "✓ Home navigation displayed"
        )

        missing_token_response = client.post(
            "/history/page-test/delete"
        )

        assert missing_token_response.status_code == 403

        routes.history_management_token = (
            "replacement-process-token"
        )

        delete_response = client.post(
            "/history/page-test/delete",
            data={
                "token": page_token,
            },
        )

        assert delete_response.status_code == 302
        remaining = test_history.read()
        assert len(remaining) == 1
        assert remaining[0]["session_id"] == "legacy-page-test"

        print("✓ Individual history deletion secured")
        print("✓ Open history forms survive an Orion restart")

        assert test_history._append(
            {
                **session,
                "session_id": "clear-one",
            }
        )

        assert test_history._append(
            {
                **session,
                "session_id": "clear-two",
            }
        )

        clear_response = client.post(
            "/history/delete-all",
            data={
                "token": page_token,
            },
        )

        assert clear_response.status_code == 302
        assert test_history.read() == []

        print("✓ Full history deletion secured")

finally:

    routes.history_store = (
        original_history_store
    )
    routes.history_management_token = (
        original_history_token
    )

print()
print(
    "✓ Playback history page test passed"
)
