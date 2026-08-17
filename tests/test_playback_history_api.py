from pathlib import Path
from tempfile import TemporaryDirectory

from app.api import routes
from app.api.server import OrionAPIServer
from app.playback.history import PlaybackHistory


print("=" * 60)
print("PLAYBACK HISTORY API TEST")
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

        first_session = {
            "session_id": "session-one",
            "started_at": (
                "2026-08-17T18:00:00+00:00"
            ),
            "playback": {
                "filename": "First.Movie.mkv",
                "fps": 24.0,
                "source": "UsenetStreamer",
            },
            "display_restored": True,
        }

        second_session = {
            "session_id": "session-two",
            "started_at": (
                "2026-08-17T19:00:00+00:00"
            ),
            "playback": {
                "filename": "Second.Movie.mkv",
                "fps": 23.976,
                "source": "UsenetStreamer",
            },
            "display_restored": True,
        }

        assert test_history._append(
            first_session
        )

        assert test_history._append(
            second_session
        )

        routes.history_store = test_history

        server = OrionAPIServer()
        client = server.app.test_client()

        response = client.get(
            "/history?limit=1"
        )

        assert response.status_code == 200

        data = response.get_json()

        assert data["count"] == 1

        assert (
            data["sessions"][0][
                "session_id"
            ]
            == "session-two"
        )

        print(
            "✓ Most recent session returned"
        )

        response = client.get(
            "/history?limit=invalid"
        )

        assert response.status_code == 400

        error = response.get_json()

        assert "error" in error

        print(
            "✓ Invalid limit rejected safely"
        )

        all_sessions = (
            test_history.read(limit=20)
        )

        assert len(all_sessions) == 2

        assert (
            all_sessions[0]["session_id"]
            == "session-two"
        )

        assert (
            all_sessions[1]["session_id"]
            == "session-one"
        )

        print(
            "✓ Sessions returned newest first"
        )

finally:

    routes.history_store = (
        original_history_store
    )

print()
print(
    "✓ Playback history API test passed"
)