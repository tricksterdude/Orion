from dataclasses import dataclass


@dataclass
class PlaybackRequest:

    title: str | None = None

    imdb_id: str | None = None

    tmdb_id: int | None = None

    filename: str | None = None

    resolution: str | None = None

    fps: float | None = None

    hdr: bool = False

    dolby_vision: bool = False

    video_codec: str | None = None

    audio_codec: str | None = None

    audio_channels: str | None = None

    bitrate: int | None = None

    source: str | None = None