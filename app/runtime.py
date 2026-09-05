import time
from queue import Empty, Queue
from threading import Event, Thread

from app.api.server import OrionAPIServer
from app.display.restore import DisplayRestore
from app.managers.provider_manager import ProviderManager
from app.media_manager import MediaManager
from app.media.session import MediaSession
from app.orion import OrionEngine
from app.playback.detector import PlaybackDetector
from app.playback.history import PlaybackHistory
from app.recovery_status import display_recovery_status


class OrionRuntime:

    PLAYBACK_REQUEST_MAX_AGE = 60

    def __init__(self):

        self.detector = PlaybackDetector()
        self.media_manager = MediaManager()

        self.restore = DisplayRestore(
            desktop_refresh=(
                self.media_manager
                .get_desktop_refresh_rate()
            )
        )
        self.media = MediaSession()
        self.engine = OrionEngine()
        self.history = PlaybackHistory()
        self.display_checkpoint_ready = False

        self.playback_requests = Queue()
        self.provider_stop_event = Event()

        self.api = OrionAPIServer(
            self.playback_received
        )

        self.providers = ProviderManager(
            self.media,
            self.playback_received,
            self.playback_stopped_received,
        )

        self.media.subscribe(self.movie_selected)

    def playback_received(self, request):

        self.playback_requests.put(
            (time.monotonic(), request)
        )

    def playback_stopped_received(self):

        self.provider_stop_event.set()

    def next_playback_request(self):

        latest = None
        now = time.monotonic()

        try:

            while True:

                received_at, request = (
                    self.playback_requests.get_nowait()
                )

                if (
                    now - received_at
                    <= self.PLAYBACK_REQUEST_MAX_AGE
                ):

                    latest = request

        except Empty:

            return latest

    def clear_playback_requests(self):

        try:

            while True:

                self.playback_requests.get_nowait()

        except Empty:

            return

    def start_playback_session(self):

        self.engine.playback_started()

        print("✓ Playback started")
        print(
            "Waiting for playback metadata..."
        )

        self.display_checkpoint_ready = (
            self.restore.save()
        )

        if self.display_checkpoint_ready:

            print(
                "✓ Display recovery checkpoint saved"
            )

        else:

            print(
                "✗ Display recovery checkpoint could "
                "not be saved"
            )
            print(
                "Automatic display switching is "
                "disabled for this session."
            )

            display_recovery_status.set(
                {
                    "status": "failed",
                    "message": (
                        "Orion could not save a display "
                        "recovery checkpoint. Automatic "
                        "display switching is disabled "
                        "for this playback session."
                    ),
                }
            )

        self.history.start()

        return self.display_checkpoint_ready

    def recover_display_if_needed(self):

        result = self.restore.recover_pending()

        display_recovery_status.set(result)
        self.display_checkpoint_ready = False

        if result["status"] == "restored":

            print(
                "✓ Interrupted display session "
                "recovered"
            )
            print(result["message"])
            print()

        elif result["status"] == "failed":

            print(
                "✗ Display recovery requires "
                "attention"
            )
            print(result["message"])
            print()

        return result

    def begin_cinema_session(self, request):

        if request.fps is None:

            self.history.attach_metadata(
                request,
            )

            print(
                "✗ Playback metadata has "
                "no FPS value"
            )

            return False

        if not self.display_checkpoint_ready:

            self.history.attach_metadata(
                request,
            )

            print(
                "✗ Display switching skipped because "
                "no recovery checkpoint is available"
            )

            return False

        print(
            "✓ Playback metadata received"
        )
        print(
            f"Source: {request.source}"
        )
        print(
            f"Using reported FPS: "
            f"{request.fps}"
        )

        result = self.engine.begin_cinema(
            request.fps
        )

        self.history.attach_metadata(
            request,
            result,
        )

        print()

        return result["switched"]

    def stop_playback_session(self):

        print("✓ Playback stopped")

        checkpoint_was_ready = (
            self.display_checkpoint_ready
        )

        if checkpoint_was_ready:

            restored = self.restore.restore()

        else:

            restored = True

        self.display_checkpoint_ready = False

        if restored and checkpoint_was_ready:

            print(
                "✓ Desktop display mode restored"
            )

        elif restored:

            print(
                "✓ Display remained unchanged; "
                "no restoration was required"
            )

        else:

            print(
                "✗ Display restoration failed"
            )

            display_recovery_status.set(
                {
                    "status": "failed",
                    "message": (
                        "Orion could not restore the "
                        "saved display mode after "
                        "playback. The recovery "
                        "checkpoint was retained and "
                        "Orion will retry at startup."
                    ),
                }
            )

        self.history.finish(restored)
        self.engine.playback_stopped()

        self.clear_playback_requests()
        self.providers.reset()

    def movie_selected(self, context):

        print()
        print("=" * 60)
        print("MOVIE SELECTED")
        print("=" * 60)
        print()

        print("Title :", context.media.title)
        print("IMDb  :", context.media.imdb_id)

        context = self.engine.analyse(context)

        if context.metadata:

            print()
            print("=" * 60)
            print("METADATA")
            print("=" * 60)
            print()

            print(
                "TMDb   :",
                context.metadata.tmdb_id,
            )
            print(
                "Rating :",
                context.metadata.vote_average,
            )

        if context.technical:

            print()
            print("=" * 60)
            print("TECHNICAL")
            print("=" * 60)
            print()

            print(
                "FPS        :",
                context.technical.fps,
            )
            print(
                "Resolution :",
                context.technical.resolution,
            )
            print(
                "HDR        :",
                context.technical.hdr,
            )
            print(
                "Video      :",
                context.technical.video_codec,
            )
            print(
                "Audio      :",
                context.technical.audio_codec,
            )

    def run(self):

        print()
        print("=" * 60)
        print("                     ORION")
        print("=" * 60)
        print()

        self.recover_display_if_needed()

        Thread(
            target=self.api.start,
            daemon=True,
        ).start()

        print(
            "✓ Orion API listening on "
            "http://127.0.0.1:8765"
        )
        print()

        self.providers.start()

        print()
        print("Monitoring playback...")
        print()

        session_active = False
        cinema_active = False

        try:

            while True:

                playback = self.detector.update()

                provider_stopped = (
                    self.provider_stop_event.is_set()
                )

                if provider_stopped:

                    self.provider_stop_event.clear()

                if (
                    (
                        playback["stopped"]
                        or provider_stopped
                    )
                    and session_active
                ):

                    self.stop_playback_session()

                    session_active = False
                    cinema_active = False

                elif (
                    playback["started"]
                    and not session_active
                ):

                    self.start_playback_session()

                    session_active = True
                    cinema_active = False

                request = self.next_playback_request()

                if request is not None:

                    if not session_active:

                        self.start_playback_session()

                        session_active = True
                        cinema_active = False

                    if not cinema_active:

                        cinema_active = (
                            self.begin_cinema_session(
                                request
                            )
                        )

                if session_active:

                    self.history.refresh_receiver()

                time.sleep(1)

        except KeyboardInterrupt:

            print()
            print("Stopping Orion...")

        finally:

            if session_active:

                self.stop_playback_session()

            self.clear_playback_requests()
            self.providers.reset()
            self.providers.stop()

            print("✓ Orion stopped")
