from app.media.models import MediaState
from app.providers.base import MediaProvider


class UsenetStreamerProvider(MediaProvider):

    @property
    def name(self):

        return "UsenetStreamer"

    def is_available(self):

        return False

    def current_media(self):

        return MediaState()