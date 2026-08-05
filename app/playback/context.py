from dataclasses import dataclass


@dataclass
class PlaybackContext:

    player: str | None = None

    source: str | None = None

    stream_url: str | None = None

    local_file: str | None = None

    started: bool = False