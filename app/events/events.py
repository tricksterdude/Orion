from dataclasses import dataclass


@dataclass
class MovieSelectedEvent:

    imdb_id: str
    title: str
    year: int | None
    player: str


@dataclass
class MetadataLoadedEvent:

    imdb_id: str
    tmdb_id: int
    title: str
    rating: float