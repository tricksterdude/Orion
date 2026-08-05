from app.media.session import MediaSession
from app.metadata.tmdb_manager import TMDbManager
from app.providers.aiostreams import AIOStreamsProvider


class OrionController:

    def __init__(self):

        self.session = MediaSession()

        self.tmdb = TMDbManager()

        self.provider = AIOStreamsProvider(self.session)

        self.session.subscribe(self.media_changed)

    def start(self):

        print()
        print("=" * 60)
        print("ORION STARTED")
        print("=" * 60)
        print()

        self.provider.start()

    def media_changed(self, state):

        print()
        print("=" * 60)
        print("MEDIA DETECTED")
        print("=" * 60)

        print()

        print("Player :", state.player)
        print("Title  :", state.title)
        print("IMDb   :", state.imdb_id)
        print("Year   :", state.year)

        if not state.imdb_id:
            return

        metadata = self.tmdb.lookup_imdb(state.imdb_id)

        if metadata is None:

            print()
            print("TMDb : No match")
            return

        print()
        print("TMDb Metadata")
        print()

        print("TMDb ID :", metadata.tmdb_id)
        print("Title   :", metadata.title)
        print("Year    :", metadata.year)
        print("Rating  :", metadata.vote_average)