import time

from app.cinema.session import CinemaSession
from app.display.restore import DisplayRestore
from app.playback.detector import PlaybackDetector


class OrionRuntime:

    def __init__(self):

        self.detector = PlaybackDetector()
        self.session = CinemaSession()
        self.restore = DisplayRestore()

        self.session_active = False

    def run(self):

        print()
        print("=" * 60)
        print("                     ORION")
        print("=" * 60)
        print()

        print("Monitoring Stremio...")
        print()

        while True:

            playback = self.detector.update()

            #
            # Stremio started
            #
            if playback["started"] and not self.session_active:

                print("✓ Stremio started")

                self.restore.save()

                #
                # Temporary hard-coded FPS.
                # We'll replace this with real FPS detection later.
                #
                self.session.begin(23.976)

                self.session_active = True

            #
            # Stremio closed
            #
            elif playback["stopped"] and self.session_active:

                print("✓ Stremio stopped")

                print("Restoring display...")

                self.restore.restore()

                self.session_active = False

            time.sleep(1)