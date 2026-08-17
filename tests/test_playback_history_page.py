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
                "title": "The Matrix",
                "filename": (
                    "The.Matrix.1999.2160p.mkv"
                ),
                "resolution": "3840x2160",
                "fps": 23.976,
                "hdr": True,
                "dolby_vision": False,
                "video_codec": "hevc",
                "source": "UsenetStreamer",
            },
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

        routes.history_store = (
            test_history
        )

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
        assert "The Matrix" in page
        assert "UsenetStreamer" in page
        assert "23.976 fps" in page
        assert "Display restored" in page

        print(
            "✓ Playback history page rendered"
        )
        print(
            "✓ Session details displayed"
        )
        print(
            "✓ Display status displayed"
        )

finally:

    routes.history_store = (
        original_history_store
    )

print()
print(
    "✓ Playback history page test passed"
)