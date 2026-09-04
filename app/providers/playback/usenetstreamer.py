import re
import subprocess
import threading
import time

from app.docker_cli import docker_executable

import psutil

from app.api.models import PlaybackRequest
from app.media.title import friendly_media_title
from app.providers.playback.base import PlaybackProvider
from app.technical.nzbdav_probe import NZBDAVProbe


class UsenetStreamerPlaybackProvider(
    PlaybackProvider
):

    name = "UsenetStreamer"

    STREAM_PORT = 7001
    CONNECTION_GRACE_SECONDS = 10
    CONNECTION_START_TIMEOUT = 20

    URL_PATTERN = re.compile(
        r"Proxying GET "
        r"(http://host\.docker\.internal:"
        r"8500/[^\r\n]+)"
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

        self._process = None
        self._thread = None
        self._connection_thread = None

        self._last_url = None
        self._stop_event = threading.Event()

    def is_available(self):

        try:

            result = subprocess.run(
                [
                    docker_executable(),
                    "ps",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                ),
            )

            return (
                "usenetstreamer"
                in result.stdout.splitlines()
            )

        except Exception:

            return False

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

        if self._process is not None:

            self._process.terminate()
            self._process = None

        self._thread = None
        self._connection_thread = None

    def reset(self):

        self._last_url = None

    @staticmethod
    def _connection_port(address):

        if not address:

            return None

        return getattr(address, "port", None)

    def _has_stream_connection(self):

        try:

            connections = psutil.net_connections(
                kind="tcp"
            )

        except (
            psutil.AccessDenied,
            psutil.Error,
            OSError,
        ):

            return False

        for connection in connections:

            if (
                connection.status
                != psutil.CONN_ESTABLISHED
            ):

                continue

            remote_port = self._connection_port(
                connection.raddr
            )

            if remote_port == self.STREAM_PORT:

                return True

        return False

    def _start_connection_monitor(self):

        if (
            self._connection_thread is not None
            and self._connection_thread.is_alive()
        ):

            return

        self._connection_thread = threading.Thread(
            target=self._monitor_connection,
            daemon=True,
        )

        self._connection_thread.start()

    def _monitor_connection(self):

        monitor_started = time.monotonic()
        last_connected = None

        while not self._stop_event.is_set():

            now = time.monotonic()

            connected = (
                self._has_stream_connection()
            )

            if connected:

                last_connected = now

            elif (
                last_connected is not None
                and (
                    now - last_connected
                    >= self.CONNECTION_GRACE_SECONDS
                )
            ):

                print(
                    "✓ UsenetStreamer playback ended"
                )

                if self.on_stopped is not None:

                    self.on_stopped()

                return

            elif (
                last_connected is None
                and (
                    now - monitor_started
                    >= self.CONNECTION_START_TIMEOUT
                )
            ):

                return

            self._stop_event.wait(1)

    def _watch(self):

        try:

            probe = NZBDAVProbe()

            self._process = subprocess.Popen(
                [
                    docker_executable(),
                    "logs",
                    "--tail",
                    "0",
                    "-f",
                    "usenetstreamer",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                ),
            )

            for line in self._process.stdout:

                if self._stop_event.is_set():

                    return

                match = self.URL_PATTERN.search(
                    line
                )

                if match is None:

                    continue

                docker_url = match.group(1)

                if docker_url == self._last_url:

                    continue

                self._last_url = docker_url

                print()
                print(
                    "✓ UsenetStreamer media detected"
                )
                print(
                    "Running FFprobe analysis..."
                )

                try:

                    technical = probe.probe(
                        docker_url
                    )

                except Exception as error:

                    print(
                        "✗ FFprobe analysis failed:"
                    )
                    print(error)

                    continue

                resolution = None

                if (
                    technical["width"]
                    and technical["height"]
                ):

                    resolution = (
                        f"{technical['width']}x"
                        f"{technical['height']}"
                    )

                title = friendly_media_title(
                    technical["filename"]
                )

                request = PlaybackRequest(
                    title=title,
                    filename=technical["filename"],
                    resolution=resolution,
                    fps=technical["fps"],
                    hdr=technical["hdr"],
                    dolby_vision=technical.get(
                        "dolby_vision",
                        False,
                    ),
                    video_codec=technical["codec"],
                    audio_codec=technical.get(
                        "audio_codec"
                    ),
                    audio_channels=technical.get(
                        "audio_channels"
                    ),
                    audio_sample_rate=technical.get(
                        "audio_sample_rate"
                    ),
                    audio_bitrate=technical.get(
                        "audio_bitrate"
                    ),
                    audio_profile=technical.get(
                        "audio_profile"
                    ),
                    immersive_audio=technical.get(
                        "immersive_audio"
                    ),
                    bitrate=technical.get("bitrate"),
                    source="UsenetStreamer",
                )

                print(
                    "✓ Technical metadata extracted"
                )
                print(
                    f"Title : {request.title}"
                )
                print(
                    f"File  : {request.filename}"
                )
                print(
                    f"FPS   : {request.fps}"
                )
                print(
                    f"Video : {request.video_codec}"
                )
                print(
                    f"Audio : {request.audio_codec}"
                )
                print(
                    f"Layout: {request.audio_channels}"
                )
                print(
                    f"Rate  : {request.audio_sample_rate} Hz"
                )
                print(
                    f"Audio bitrate: {request.audio_bitrate}"
                )
                print(
                    f"Immersive: {request.immersive_audio}"
                )
                print(
                    f"HDR   : {request.hdr}"
                )
                print()

                if self.on_playback is not None:

                    self.on_playback(request)

                self._start_connection_monitor()

        except Exception as error:

            if self._stop_event.is_set():

                return

            print()
            print(
                "✗ UsenetStreamer provider failed:"
            )
            print(error)
