from app.providers.playback.base import PlaybackProvider


class UsenetStreamerPlaybackProvider(PlaybackProvider):

    name = "UsenetStreamer"

    def is_available(self):

        return False

    def start(self):

        pass

    def stop(self):

        pass