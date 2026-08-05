from dataclasses import dataclass

from app.media.models import MediaState


@dataclass
class MovieContext:

    media: MediaState

    metadata: object | None = None

    technical: object | None = None

    cinema: object | None = None