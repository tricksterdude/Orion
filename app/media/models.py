from dataclasses import dataclass


@dataclass
class MediaState:

    player: str | None = None

    title: str | None = None

    imdb_id: str | None = None

    year: int | None = None

    artist: str | None = None

    playing: bool = False

    paused: bool = False

    stopped: bool = True