from app.technical.ffprobe_metadata import (
    analyse_ffprobe_document,
    parse_frame_rate,
)


print("=" * 60)
print("FFPROBE AUDIO METADATA TEST")
print("=" * 60)
print()


document = {
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "hevc",
            "width": 3840,
            "height": 2160,
            "avg_frame_rate": "24000/1001",
            "r_frame_rate": "24000/1001",
            "color_transfer": "smpte2084",
            "color_primaries": "bt2020",
        },
        {
            "codec_type": "audio",
            "codec_name": "truehd",
            "codec_long_name": "TrueHD",
            "profile": "Dolby TrueHD + Dolby Atmos",
            "channels": 8,
            "channel_layout": "7.1",
            "sample_rate": "48000",
            "bit_rate": "4800000",
            "tags": {
                "title": "Dolby Atmos 7.1",
            },
        },
    ],
    "format": {
        "bit_rate": "61500000",
    },
}

metadata = analyse_ffprobe_document(
    document,
    filename="Film.2160p.DV.TrueHD.Atmos.mkv",
    source_host="localhost",
)

assert metadata["fps"] == 23.976
assert metadata["codec"] == "hevc"
assert metadata["hdr"] is True
assert metadata["dolby_vision"] is True
assert metadata["audio_codec"] == "Dolby TrueHD"
assert metadata["audio_profile"] == (
    "Dolby TrueHD + Dolby Atmos"
)
assert metadata["immersive_audio"] == "Dolby Atmos"
assert metadata["audio_channels"] == "7.1"
assert metadata["audio_sample_rate"] == 48000
assert metadata["audio_bitrate"] == 4800000
assert metadata["bitrate"] == 61500000

print("✓ Video and lossless Atmos metadata extracted")


dtsx = analyse_ffprobe_document(
    {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "25/1",
            },
            {
                "codec_type": "audio",
                "codec_name": "dts",
                "channels": 6,
                "sample_rate": "48000",
                "tags": {
                    "title": "DTS:X Master Audio",
                },
            },
        ]
    },
    filename="Film.DTS-HD.MA.DTS-X.mkv",
)

assert dtsx["audio_codec"] == "DTS-HD Master Audio"
assert dtsx["immersive_audio"] == "DTS:X"
assert dtsx["audio_channels"] == "6 channels"

print("✓ DTS-HD and DTS:X markers recognised")


default_audio = analyse_ffprobe_document(
    {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "hevc",
                "avg_frame_rate": "24/1",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "disposition": {"default": 0},
            },
            {
                "codec_type": "audio",
                "codec_name": "eac3",
                "profile": "Dolby Digital Plus + Dolby Atmos",
                "disposition": {"default": 1},
            },
        ]
    }
)

assert default_audio["audio_codec"] == "Dolby Digital Plus"
assert default_audio["immersive_audio"] == "Dolby Atmos"

print("✓ Default audio track preferred when multiple tracks exist")


without_audio = analyse_ffprobe_document(
    {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1280,
                "height": 720,
                "avg_frame_rate": "0/0",
            }
        ]
    }
)

assert without_audio["audio_codec"] is None
assert without_audio["audio_channels"] is None
assert without_audio["fps"] is None
assert parse_frame_rate("invalid") is None

print("✓ Missing or invalid metadata fails safely")
print()
print("✓ FFprobe audio metadata test passed")
