from app.providers.playback.base import PlaybackProvider


class AIOStreamsPlaybackProvider(PlaybackProvider):

    name = "AIOStreams"

    def __init__(self, session):

        super().__init__(session)

        self._current = None

    def is_available(self):

        return True

    def start(self):

        pass

    def stop(self):

        pass

    def current(self):

        return self._current