from app.media.context import MovieContext
from app.media.models import MediaState


class PlaybackSession:

    def __init__(self):

        self.reset()

    def reset(self):

        self.active = False

        self.context = MovieContext(
            media=MediaState()
        )

        self.original_refresh = None

        self.current_refresh = None

    def start(self):

        self.active = True

    def stop(self):

        self.reset()

    def current(self):

        return self.context

    def set_context(self, context):

        self.context = context

    def is_active(self):

        return self.active