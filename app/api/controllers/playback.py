from app.api.models import PlaybackRequest


class PlaybackController:

    def play(self, request: PlaybackRequest):

        print()
        print("=" * 60)
        print("PLAYBACK API")
        print("=" * 60)
        print()

        print("Title :", request.title)
        print("IMDb  :", request.imdb_id)
        print("File  :", request.filename)