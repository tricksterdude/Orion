from app.media.context import MovieContext
from app.media.models import MediaState


class MediaSession:

    def __init__(self):

        self.context = MovieContext(
            media=MediaState()
        )

        self._listeners = []

    def update(self, state: MediaState):

        self.context.media = state

        for listener in self._listeners:

            listener(self.context)

    def update_metadata(self, metadata):

        self.context.metadata = metadata

    def current(self):

        return self.context

    def subscribe(self, callback):

        self._listeners.append(callback)