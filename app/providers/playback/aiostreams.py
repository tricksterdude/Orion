import os
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import psutil

from app.api.models import PlaybackRequest
from app.providers.playback.base import PlaybackProvider
from app.technical.stremio_probe import StremioProbe


class AIOStreamsPlaybackProvider(PlaybackProvider):

    name = "AIOStreams"

    DEBUG_ARGUMENTS = (
        "--remote-debugging-port=9222"
    )

    def __init__(
        self,
        session,
        on_playback=None,
        on_stopped=None,
    ):

        super().__init__(session)

        self.on_playback = on_playback
        self.on_stopped = on_stopped

        self.probe = StremioProbe()

        self._thread = None
        self._stop_event = threading.Event()
        self._last_url = None
        self._playing = False
        self._stremio_process = None

    def is_available(self):

        return self.stremio_path().exists()

    def start(self):

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._watch,
            daemon=True,
        )

        self._thread.start()

    def stop(self):

        self._stop_event.set()

        if self._stremio_process is not None:

            try:

                self._stremio_process.terminate()

            except OSError:

                pass

            self._stremio_process = None

        self._thread = None

    def reset(self):

        self._last_url = None
        self._playing = False

    def _notify_stopped(self):

        if not self._playing:

            return

        self._playing = False
        self._last_url = None

        if self.on_stopped is not None:

            self.on_stopped()

    def _watch(self):

        if not self.ensure_debug_stremio():

            if not self._stop_event.is_set():

                print()
                print(
                    "✗ AIOStreams provider unavailable"
                )
                print(
                    "Close Stremio before starting Orion."
                )
                print()

            return

        while not self._stop_event.is_set():

            if not self.probe.debugger_available():

                self._notify_stopped()
                return

            try:

                selected = (
                    self.probe.selected_stream()
                )

            except Exception:

                if not self.probe.debugger_available():

                    self._notify_stopped()
                    return

                time.sleep(1)
                continue

            if selected is None:

                self._notify_stopped()
                time.sleep(1)
                continue

            self._playing = True

            stream_url = selected["url"]
            parsed = urlparse(stream_url)

            if parsed.hostname in {
                "localhost",
                "127.0.0.1",
            }:

                self._last_url = None
                time.sleep(1)
                continue

            if stream_url == self._last_url:

                time.sleep(1)
                continue

            self._last_url = stream_url

            print()
            print(
                "✓ AIOStreams media detected"
            )
            print(
                "Running direct FFprobe analysis..."
            )

            try:

                technical = self.probe.analyse(
                    selected
                )

                resolution = None

                if (
                    technical["width"]
                    and technical["height"]
                ):

                    resolution = (
                        f"{technical['width']}x"
                        f"{technical['height']}"
                    )

                request = PlaybackRequest(
                    filename=technical["filename"],
                    resolution=resolution,
                    fps=technical["fps"],
                    hdr=technical["hdr"],
                    dolby_vision=technical[
                        "dolby_vision"
                    ],
                    video_codec=technical["codec"],
                    source="AIOStreams",
                )

                print(
                    "✓ Technical metadata extracted"
                )
                print(
                    f"File  : {request.filename}"
                )
                print(
                    f"Host  : "
                    f"{technical['source_host']}"
                )
                print(
                    f"FPS   : {request.fps}"
                )
                print(
                    f"Video : {request.video_codec}"
                )
                print(
                    f"HDR   : {request.hdr}"
                )
                print(
                    f"DV    : "
                    f"{request.dolby_vision}"
                )
                print()

                if self.on_playback is not None:

                    self.on_playback(request)

            except Exception as error:

                print()
                print(
                    "✗ AIOStreams analysis failed:"
                )
                print(error)
                print()

            time.sleep(1)

    def ensure_debug_stremio(self):

        if self.probe.debugger_available():

            return True

        if self.stremio_running():

            return False

        environment = os.environ.copy()

        environment[
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"
        ] = self.DEBUG_ARGUMENTS

        self._stremio_process = subprocess.Popen(
            [str(self.stremio_path())],
            env=environment,
        )

        for _ in range(30):

            if self._stop_event.is_set():

                return False

            if self.probe.debugger_available():

                return True

            time.sleep(1)

        return False

    @staticmethod
    def stremio_running():

        for process in psutil.process_iter(
            ["name"]
        ):

            try:

                name = process.info["name"]

                if (
                    name
                    and "stremio-shell-ng"
                    in name.lower()
                ):

                    return True

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):

                continue

        return False

    @staticmethod
    def stremio_path():

        return (
            Path(os.environ["LOCALAPPDATA"])
            / "Programs"
            / "Stremio"
            / "stremio-shell-ng.exe"
        )