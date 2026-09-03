import json
import tempfile
from pathlib import Path

from app.providers.playback.aiostreams import (
    AIOStreamsPlaybackProvider,
)


print("=" * 60)
print("AIOSTREAMS LOCAL PLAYBACK TEST")
print("=" * 60)
print()

with tempfile.TemporaryDirectory() as folder:

    services_path = (
        Path(folder) / "services.json"
    )
    services_path.write_text(
        json.dumps(
            {
                "services": [
                    {
                        "name": "AIOStreams",
                        "container": "aiostreams",
                        "port": 3500,
                        "url": (
                            "http://localhost:3500"
                        ),
                    },
                    {
                        "name": "UsenetStreamer",
                        "container": (
                            "usenetstreamer"
                        ),
                        "port": 7001,
                        "url": (
                            "http://localhost:7001"
                        ),
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    provider = AIOStreamsPlaybackProvider(
        session=object(),
        services_path=services_path,
    )

    assert provider._supports_stream_url(
        "https://stream.example/video.mkv"
    )
    assert provider._supports_stream_url(
        "http://localhost:3500/playback/video"
    )
    assert provider._supports_stream_url(
        "http://127.0.0.1:3500/playback/video"
    )
    assert not provider._supports_stream_url(
        "http://localhost:7001/playback/video"
    )
    assert not provider._supports_stream_url(
        "http://127.0.0.1:12460/video"
    )

print("✓ Configured local AIOStreams URLs accepted")
print("✓ Other local service URLs remain ignored")

with tempfile.TemporaryDirectory() as folder:

    provider = AIOStreamsPlaybackProvider(
        session=object(),
        services_path=(
            Path(folder) / "missing.json"
        ),
    )

    assert not provider._supports_stream_url(
        "http://localhost:3500/playback/video"
    )

print("✓ Missing service configuration fails closed")
print()
print("✓ AIOStreams local playback test passed")
