from app.events.events import MetadataLoadedEvent


class LoggerSubscriber:

    def __init__(self, bus):

        bus.subscribe(

            MetadataLoadedEvent,

            self.metadata_loaded,
        )

    def metadata_loaded(self, event):

        print()

        print("=" * 60)
        print("METADATA LOADED")
        print("=" * 60)

        print()

        print("IMDb   :", event.imdb_id)
        print("TMDb   :", event.tmdb_id)
        print("Title  :", event.title)
        print("Rating :", event.rating)