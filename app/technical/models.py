from dataclasses import dataclass


@dataclass
class TechnicalMetadata:

    fps: float | None = None

    resolution: str | None = None

    hdr: bool = False

    dolby_vision: bool = False

    video_codec: str | None = None

    audio_codec: str | None = None

    audio_channels: str | None = None

    audio_sample_rate: int | None = None

    audio_bitrate: int | None = None

    audio_profile: str | None = None

    immersive_audio: str | None = None

    bitrate: int | None = None
