import re
import subprocess
import threading

from app.api.models import PlaybackRequest
from app.providers.playback.base import PlaybackProvider
from app.technical.nzbdav_probe import NZBDAVProbe


class UsenetStreamerPlaybackProvider(
    PlaybackProvider
):

    name = "UsenetStreamer"

    URL_PATTERN = re.compile(
        r"Proxying GET "
        r"(http://host\.docker\.internal:"
        r"8500/[^\r\n]+)"
    )

    def __init__(
        self,
        session,
        on_playback=None,
    ):

        super().__init__(session)

        self.on_playback = on_playback
        self._process = None
        self._thread = None
        self._last_url = None

    def is_available(self):

        try:

            result = subprocess.run(
                [
                    "docker",
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

        if self._thread is not None:

            return

        self._thread = threading.Thread(
            target=self._watch,
            daemon=True,
        )

        self._thread.start()

    def stop(self):

        if self._process is not None:

            self._process.terminate()
            self._process = None

        self._thread = None

    def reset(self):

        self._last_url = None

    def _watch(self):

        try:

            probe = NZBDAVProbe()

            self._process = subprocess.Popen(
                [
                    "docker",
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

                request = PlaybackRequest(
                    filename=technical["filename"],
                    resolution=resolution,
                    fps=technical["fps"],
                    hdr=technical["hdr"],
                    video_codec=technical["codec"],
                    source="UsenetStreamer",
                )

                print(
                    "✓ Technical metadata extracted"
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
                    f"HDR   : {request.hdr}"
                )
                print()

                if self.on_playback is not None:

                    self.on_playback(request)

        except Exception as error:

            print()
            print(
                "✗ UsenetStreamer provider failed:"
            )
            print(error)