from dataclasses import dataclass


@dataclass
class MovieMetadata:

    imdb_id: str = ""
    tmdb_id: int = 0

    title: str = ""
    original_title: str = ""

    year: int = 0

    overview: str = ""

    poster: str = ""
    backdrop: str = ""

    vote_average: float = 0.0

    media_type: str = ""