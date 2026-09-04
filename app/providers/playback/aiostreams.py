import json
import os
import threading
from pathlib import Path
from urllib.parse import urlparse

from app.api.models import PlaybackRequest
from app.local_configuration import services_config_path
from app.providers.playback.base import PlaybackProvider
from app.technical.stremio_probe import StremioProbe


class AIOStreamsPlaybackProvider(PlaybackProvider):

    name = "AIOStreams"

    def __init__(
        self,
        session,
        on_playback=None,
        on_stopped=None,
        services_path=None,
    ):

        super().__init__(session)

        self.on_playback = on_playback
        self.on_stopped = on_stopped

        self.probe = StremioProbe()

        self.services_path = Path(
            services_path
            or services_config_path()
        )

        self._thread = None
        self._stop_event = threading.Event()
        self._last_url = None
        self._playing = False

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

    def _wait(self, seconds=1):

        return self._stop_event.wait(
            seconds
        )

    def _local_aiostreams_ports(self):

        try:

            payload = json.loads(
                self.services_path.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            ValueError,
            TypeError,
        ):

            return set()

        if not isinstance(payload, dict):

            return set()

        ports = set()

        for service in payload.get(
            "services",
            [],
        ):

            if not isinstance(service, dict):

                continue

            identifiers = {
                str(service.get("name", ""))
                .strip()
                .lower(),
                str(service.get("container", ""))
                .strip()
                .lower(),
            }

            if "aiostreams" not in identifiers:

                continue

            try:

                parsed = urlparse(
                    str(service.get("url", ""))
                )
                hostname = (
                    parsed.hostname or ""
                ).lower()

                if hostname not in {
                    "localhost",
                    "127.0.0.1",
                    "::1",
                }:

                    continue

                port = (
                    parsed.port
                    or service.get("port")
                )

                if port is not None:

                    ports.add(int(port))

            except (TypeError, ValueError):

                continue

        return ports

    def _supports_stream_url(self, stream_url):

        parsed = urlparse(stream_url)
        hostname = (
            parsed.hostname or ""
        ).lower()

        if hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:

            return True

        try:

            port = parsed.port

        except ValueError:

            return False

        return (
            port is not None
            and port
            in self._local_aiostreams_ports()
        )

    def _watch(self):

        while not self._stop_event.is_set():

            if not self.probe.debugger_available():

                self._notify_stopped()
                self._last_url = None
                self._wait(2)

                continue

            try:

                selected = (
                    self.probe.selected_stream()
                )

            except Exception:

                if not self.probe.debugger_available():

                    self._notify_stopped()
                    self._last_url = None

                self._wait()
                continue

            if selected is None:

                self._notify_stopped()
                self._wait()

                continue

            self._playing = True

            stream_url = selected["url"]

            if not self._supports_stream_url(
                stream_url
            ):

                self._last_url = None
                self._wait()

                continue

            if stream_url == self._last_url:

                self._wait()
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

            self._wait()

    @staticmethod
    def stremio_path():

        return (
            Path(os.environ["LOCALAPPDATA"])
            / "Programs"
            / "Stremio"
            / "stremio-shell-ng.exe"
        )
