from app.events.events import MovieSelectedEvent, MetadataLoadedEvent


class TMDbSubscriber:

    def __init__(self, bus, tmdb):

        self.bus = bus
        self.tmdb = tmdb

        bus.subscribe(MovieSelectedEvent, self.movie_selected)

    def movie_selected(self, event):

        metadata = self.tmdb.lookup_imdb(event.imdb_id)

        if metadata is None:
            return

        self.bus.publish(

            MetadataLoadedEvent(

                imdb_id=event.imdb_id,

                tmdb_id=metadata.tmdb_id,

                title=metadata.title,

                rating=metadata.vote_average,
            )

        )