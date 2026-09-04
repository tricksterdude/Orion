import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.api.models import PlaybackRequest
from app.audio.windows_output import AudioEndpoint
from app.display.mode import DisplayMode
from app.playback.history import PlaybackHistory


print("=" * 60)
print("PLAYBACK HISTORY TEST")
print("=" * 60)
print()


class FakeAudioOutput:

    def default_endpoint(self):

        return AudioEndpoint(
            name="DENON-AVR HDMI",
            active=True,
            form_factor="HDMI/display audio",
        )


class FakeSpatialProcessors:

    def recommendation(self, immersive_audio):

        assert immersive_audio == "Dolby Atmos"

        return {
            "policy": "Automatic",
            "processor": "Dolby Access",
            "installed": True,
            "control": "observe_only",
        }

with TemporaryDirectory() as temporary_directory:

    history_path = (
        Path(temporary_directory)
        / "playback_history.jsonl"
    )

    history = PlaybackHistory(
        history_path,
        audio_output=FakeAudioOutput(),
        spatial_processors=FakeSpatialProcessors(),
    )

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
        audio_sample_rate=48000,
        audio_bitrate=4000000,
        audio_profile="Dolby TrueHD",
        immersive_audio="Dolby Atmos",
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
    assert record["playback"]["audio_codec"] == "truehd"
    assert record["playback"]["audio_sample_rate"] == 48000
    assert record["playback"]["immersive_audio"] == "Dolby Atmos"
    assert record["audio_output"]["name"] == "DENON-AVR HDMI"
    assert record["audio_processing"]["processor"] == "Dolby Access"
    assert record["audio_processing"]["control"] == "observe_only"

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

    history.start()

    history.attach_metadata(request)

    saved_without_cinema = history.finish(
        restored=True
    )

    assert saved_without_cinema is True

    metadata_only_record = history.read()[0]

    assert (
        metadata_only_record["playback"]["title"]
        == "The Matrix"
    )
    assert metadata_only_record["cinema"] is None

    print(
        "✓ Metadata retained without a display change"
    )

    for index in range(20):

        assert history._append(
            {
                "session_id": f"session-{index}",
                "started_at": f"2026-08-19T{index:02d}:00:00+00:00",
            }
        )

    retained = history.read(limit=100)

    assert len(retained) == 15
    assert retained[0]["session_id"] == "session-19"
    assert retained[-1]["session_id"] == "session-5"

    stored_lines = history_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(stored_lines) == 15

    print("✓ Playback history retains no more than 15 entries")

    assert history.delete("session-10") is True
    assert history.delete("missing-session") is False

    remaining = history.read(limit=100)

    assert len(remaining) == 14
    assert all(
        item["session_id"] != "session-10"
        for item in remaining
    )

    print("✓ Individual playback history entry deleted")

    assert history.clear() == 14
    assert history.read() == []

    print("✓ All playback history deleted")
