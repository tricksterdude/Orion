from app.cinema.session import CinemaSession
from app.metadata.tmdb_manager import TMDbManager
from app.playback.session import PlaybackSession
from app.technical.manager import TechnicalManager


class OrionEngine:

    def __init__(self):

        self.playback = PlaybackSession()

        self.tmdb = TMDbManager()

        self.technical = TechnicalManager()

        self.cinema = CinemaSession()

    def analyse(self, context):

        #
        # Store latest playback context.
        #
        self.playback.set_context(context)

        #
        # Metadata
        #
        context = self.tmdb.analyse(context)

        #
        # Technical
        #
        context = self.technical.analyse(context)

        return context

    def playback_started(self):

        self.playback.start()

    def playback_stopped(self):

        self.playback.stop()

    def begin_cinema(self, fps):

        analysis = self.cinema.begin(fps)

        self.playback.current().cinema = analysis

        return analysis

    def current(self):

        return self.playback.current()