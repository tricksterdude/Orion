import json
import subprocess

import app.technical.nzbdav_probe as nzbdav_module
import app.technical.stremio_probe as stremio_module
from app.technical.nzbdav_probe import NZBDAVProbe
from app.technical.stremio_probe import StremioProbe


print("=" * 60)
print("MEDIA FFPROBE COMMAND TEST")
print("=" * 60)
print()


PROBE_DOCUMENT = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "hevc",
            "width": 3840,
            "height": 2160,
            "avg_frame_rate": "24000/1001",
            "color_transfer": "smpte2084",
        },
        {
            "codec_type": "audio",
            "codec_name": "eac3",
            "profile": "E-AC-3+Atmos",
            "channels": 6,
            "channel_layout": "5.1(side)",
            "sample_rate": "48000",
            "bit_rate": "768000",
        },
    ],
    "format": {
        "bit_rate": "18000000",
    },
}

commands = []


def run(command, **options):

    commands.append((command, options))

    return subprocess.CompletedProcess(
        command,
        0,
        stdout=json.dumps(PROBE_DOCUMENT),
        stderr="",
    )


original_stremio_run = stremio_module.subprocess.run
original_stremio_ffprobe = stremio_module.ffprobe_executable
original_nzbdav_run = nzbdav_module.subprocess.run
original_nzbdav_ffprobe = nzbdav_module.ffprobe_executable

try:

    stremio_module.subprocess.run = run
    stremio_module.ffprobe_executable = lambda: "ffprobe.exe"
    nzbdav_module.subprocess.run = run
    nzbdav_module.ffprobe_executable = lambda: "ffprobe.exe"

    stremio = StremioProbe().analyse(
        {
            "url": "http://localhost:3500/video.mkv",
            "filename": "Film.EAC3.Atmos.mkv",
            "source_host": "localhost",
        }
    )

    assert stremio["audio_codec"] == "Dolby Digital Plus"
    assert stremio["immersive_audio"] == "Dolby Atmos"
    assert stremio["audio_channels"] == "5.1(side)"
    assert stremio["audio_sample_rate"] == 48000

    nzbdav = NZBDAVProbe.__new__(NZBDAVProbe)
    nzbdav.username = "user"
    nzbdav.password = "password"
    usenet = nzbdav.probe(
        "http://host.docker.internal:8500/Film.EAC3.Atmos.mkv"
    )

    assert usenet["audio_codec"] == "Dolby Digital Plus"
    assert usenet["immersive_audio"] == "Dolby Atmos"
    assert usenet["audio_bitrate"] == 768000

    for command, options in commands:

        assert "-select_streams" not in command
        assert "-show_entries" in command
        entries = command[
            command.index("-show_entries") + 1
        ]
        assert "codec_type" in entries
        assert "channel_layout" in entries
        assert "sample_rate" in entries
        assert "stream_tags" in entries
        assert options["timeout"] == 60

    assert any(
        "Authorization: Basic" in part
        for part in commands[1][0]
    )

    print("✓ AIOStreams probe requests video and audio streams")
    print("✓ UsenetStreamer probe preserves authenticated access")
    print("✓ Both probes return shared audio metadata")

finally:

    stremio_module.subprocess.run = original_stremio_run
    stremio_module.ffprobe_executable = original_stremio_ffprobe
    nzbdav_module.subprocess.run = original_nzbdav_run
    nzbdav_module.ffprobe_executable = original_nzbdav_ffprobe

print()
print("✓ Media FFprobe command test passed")
