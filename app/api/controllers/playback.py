from app.api.models import PlaybackRequest


class PlaybackController:

    def __init__(self, on_playback=None):

        self.on_playback = on_playback

    def set_handler(self, on_playback):

        self.on_playback = on_playback

    def play(self, request: PlaybackRequest):

        print()
        print("=" * 60)
        print("PLAYBACK API")
        print("=" * 60)
        print()

        print("Title :", request.title)
        print("IMDb  :", request.imdb_id)
        print("File  :", request.filename)
        print("FPS   :", request.fps)

        if self.on_playback is not None:

            self.on_playback(request)