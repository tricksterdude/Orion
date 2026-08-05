from dataclasses import dataclass


@dataclass
class StreamInfo:

    provider: str | None = None

    title: str | None = None

    imdb_id: str | None = None

    url: str | None = None

    local_file: str | None = None

    mime_type: str |None = None

    fps: float | None = None

    hdr: bool | None = None

    video_codec: str | None = None

    audio_codec: str | None = None