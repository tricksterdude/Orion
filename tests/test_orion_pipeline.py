import time

from app.media.session import MediaSession
from app.metadata.tmdb_manager import TMDbManager
from app.providers.aiostreams import AIOStreamsProvider


session = MediaSession()
tmdb = TMDbManager()


def media_changed(state):

    print()
    print("=" * 60)
    print("MEDIA EVENT")
    print("=" * 60)

    print()

    print("Player :", state.player)
    print("Title  :", state.title)
    print("IMDb   :", state.imdb_id)

    if not state.imdb_id:
        return

    metadata = tmdb.lookup_imdb(state.imdb_id)

    session.update_metadata(metadata)

    print()
    print("=" * 60)
    print("TMDB")
    print("=" * 60)

    print()

    print("TMDb ID :", metadata.tmdb_id)
    print("Title   :", metadata.title)
    print("Year    :", metadata.year)
    print("Rating  :", metadata.vote_average)

    print()

    print("Stored in MediaSession:",
          session.metadata.title)


session.subscribe(media_changed)

provider = AIOStreamsProvider(session)

provider.start()

print()
print("=" * 60)
print("ORION PIPELINE")
print("=" * 60)
print()

while True:
    time.sleep(1)