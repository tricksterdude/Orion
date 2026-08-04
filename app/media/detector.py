from app.media.models import MediaState


class MediaDetector:

    def current(self) -> MediaState:

        return MediaState()