import time

from app.display.restore import DisplayRestore
from app.managers.provider_manager import ProviderManager
from app.media.session import MediaSession
from app.orion.engine import OrionEngine
from app.playback.detector import PlaybackDetector


class OrionRuntime:

    def __init__(self):

        self.detector = PlaybackDetector()

        self.restore = DisplayRestore()

        self.media = MediaSession()

        self.engine = OrionEngine()

        self.providers = ProviderManager(self.media)

        self.media.subscribe(self.movie_selected)

    def movie_selected(self, context):

        context = self.engine.analyse(context)

        media = context.media

        print()
        print("=" * 60)
        print("MOVIE SELECTED")
        print("=" * 60)
        print()

        print("Title :", media.title)
        print("IMDb  :", media.imdb_id)

        if context.metadata:

            print()
            print("=" * 60)
            print("METADATA")
            print("=" * 60)
            print()

            print("TMDb   :", context.metadata.tmdb_id)
            print("Rating :", context.metadata.vote_average)

        if context.technical:

            print()
            print("=" * 60)
            print("TECHNICAL")
            print("=" * 60)
            print()

            print("FPS        :", context.technical.fps)
            print("Resolution :", context.technical.resolution)
            print("HDR        :", context.technical.hdr)
            print("Video      :", context.technical.video_codec)
            print("Audio      :", context.technical.audio_codec)

    def run(self):

        print()
        print("=" * 60)
        print("                     ORION")
        print("=" * 60)
        print()

        self.providers.start()

        print()
        print("Monitoring playback...")
        print()

        session_active = False

        while True:

            playback = self.detector.update()

            if playback["started"] and not session_active:

                self.engine.playback_started()

                print("✓ Playback started")

                self.restore.save()

                self.engine.begin_cinema(23.976)

                session_active = True

            elif playback["stopped"] and session_active:

                print("✓ Playback stopped")

                self.restore.restore()

                self.engine.playback_stopped()

                session_active = False

            time.sleep(1)