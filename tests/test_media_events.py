import time

from app.media.session import MediaSession
from app.providers.aiostreams import AIOStreamsProvider


def media_changed(state):

    print()
    print("=" * 60)
    print("MEDIA SESSION UPDATED")
    print("=" * 60)

    print(f"Player : {state.player}")
    print(f"Title  : {state.title}")
    print(f"IMDb   : {state.imdb_id}")
    print(f"Year   : {state.year}")


session = MediaSession()

session.subscribe(media_changed)

provider = AIOStreamsProvider(session)

provider.start()

print("Waiting for media events...")

while True:
    time.sleep(1)