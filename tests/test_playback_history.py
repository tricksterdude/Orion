import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.api.models import PlaybackRequest
from app.display.mode import DisplayMode
from app.playback.history import PlaybackHistory


print("=" * 60)
print("PLAYBACK HISTORY TEST")
print("=" * 60)
print()

with TemporaryDirectory() as temporary_directory:

    history_path = (
        Path(temporary_directory)
        / "playback_history.jsonl"
    )

    history = PlaybackHistory(history_path)

    request = PlaybackRequest(
        title="The Matrix",
        imdb_id="tt0133093",
        filename=(
            "The.Matrix.1999.2160p."
            "BluRay.mkv"
        ),
        resolution="3840x2160",
        fps=23.976,
        hdr=True,
        dolby_vision=False,
        video_codec="hevc",
        audio_codec="truehd",
        audio_channels="7.1",
        source="Test Provider",
    )

    cinema_result = {
        "current": DisplayMode(
            width=3840,
            height=2160,
            refresh=120,
            bits=32,
        ),
        "target": DisplayMode(
            width=3840,
            height=2160,
            refresh=23,
            bits=32,
        ),
        "supported": True,
        "simulation": False,
        "switched": True,
    }

    history.start()

    history.attach_metadata(
        request,
        cinema_result,
    )

    saved = history.finish(restored=True)

    assert saved is True
    assert history_path.exists()

    lines = history_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    record = json.loads(lines[0])

    assert record["session_id"]
    assert record["started_at"]
    assert record["ended_at"]
    assert record["duration_seconds"] is not None
    assert record["display_restored"] is True

    assert (
        record["playback"]["title"]
        == "The Matrix"
    )

    assert (
        record["playback"]["fps"]
        == 23.976
    )

    assert (
        record["playback"]["source"]
        == "Test Provider"
    )

    assert (
        record["cinema"]["current_mode"][
            "refresh"
        ]
        == 120
    )

    assert (
        record["cinema"]["target_mode"][
            "refresh"
        ]
        == 23
    )

    assert record["cinema"]["switched"] is True

    print("Saved playback:")
    print(
        record["playback"]["title"]
    )
    print()

    print("FPS:")
    print(
        record["playback"]["fps"]
    )
    print()

    print("Display change:")
    print(
        f'{record["cinema"]["current_mode"]["refresh"]}'
        " Hz -> "
        f'{record["cinema"]["target_mode"]["refresh"]}'
        " Hz"
    )
    print()

    print("Display restored:")
    print(
        record["display_restored"]
    )
    print()

    print("✓ Playback history test passed")