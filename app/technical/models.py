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

    bitrate: int | None = None