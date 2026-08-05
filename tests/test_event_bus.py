from app.events.event_bus import EventBus
from app.events.events import MovieSelectedEvent


bus = EventBus()


def on_movie(event):

    print()
    print("Movie event received")
    print()

    print(event)


bus.subscribe(MovieSelectedEvent, on_movie)

bus.publish(

    MovieSelectedEvent(

        imdb_id="tt0133093",

        title="The Matrix",

        year=1999,

        player="AIOStreams",
    )

)