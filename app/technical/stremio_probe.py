import base64
import json
import subprocess
import zlib
from fractions import Fraction
from urllib.parse import unquote, urlparse

import requests
import websocket

from app.ffprobe_cli import ffprobe_executable


class StremioProbe:

    DEBUG_URL = "http://127.0.0.1:9222/json"

    def debugger_available(self):

        try:

            self._page_target()

            return True

        except Exception:

            return False

    def selected_stream(self):

        page = self._page_target()

        socket = websocket.create_connection(
            page["webSocketDebuggerUrl"],
            timeout=5,
            suppress_origin=True,
        )

        try:

            socket.send(
                json.dumps(
                    {
                        "id": 1,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": (
                                "window.location.href"
                            ),
                            "returnByValue": True,
                        },
                    }
                )
            )

            while True:

                response = json.loads(
                    socket.recv()
                )

                if response.get("id") == 1:

                    break

        finally:

            socket.close()

        location = (
            response["result"]
            ["result"]
            ["value"]
        )

        fragment = urlparse(location).fragment

        parts = fragment.split("/")

        if len(parts) < 3:

            return None

        if parts[1] != "player":

            return None

        encoded_stream = unquote(parts[2])

        padding = "=" * (
            (-len(encoded_stream)) % 4
        )

        compressed = (
            base64.urlsafe_b64decode(
                encoded_stream + padding
            )
        )

        stream = json.loads(
            zlib.decompress(compressed)
        )

        stream_url = stream.get("url")

        if not stream_url:

            return None

        behavior = stream.get(
            "behaviorHints",
            {},
        )

        return {
            "url": stream_url,
            "name": stream.get("name"),
            "filename": behavior.get(
                "filename"
            ),
            "video_size": behavior.get(
                "videoSize"
            ),
            "source_host": urlparse(
                stream_url
            ).hostname,
        }

    def analyse(self, selected):

        result = subprocess.run(
            [
                ffprobe_executable(),
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                (
                    "stream=codec_name,width,height,"
                    "r_frame_rate,avg_frame_rate,"
                    "color_transfer,color_primaries"
                ),
                "-of",
                "json",
                selected["url"],
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
            ),
        )

        if result.returncode != 0:

            raise RuntimeError(
                result.stderr.strip()
                or "FFprobe failed"
            )

        data = json.loads(result.stdout)

        streams = data.get("streams", [])

        if not streams:

            raise RuntimeError(
                "FFprobe found no video stream"
            )

        video = streams[0]

        frame_rate = (
            video.get("avg_frame_rate")
            or video.get("r_frame_rate")
        )

        fps = self.parse_frame_rate(
            frame_rate
        )

        transfer = (
            video.get("color_transfer")
            or ""
        ).lower()

        filename = (
            selected.get("filename")
            or ""
        )

        filename_upper = filename.upper()

        dolby_vision = (
            ".DV." in filename_upper
            or "DOLBY.VISION" in filename_upper
        )

        hdr = transfer in {
            "smpte2084",
            "arib-std-b67",
        }

        return {
            "filename": filename or None,
            "source_host": selected.get(
                "source_host"
            ),
            "fps": fps,
            "width": video.get("width"),
            "height": video.get("height"),
            "codec": video.get("codec_name"),
            "color_transfer": transfer,
            "color_primaries": video.get(
                "color_primaries"
            ),
            "hdr": hdr,
            "dolby_vision": dolby_vision,
        }

    def _page_target(self):

        targets = requests.get(
            self.DEBUG_URL,
            timeout=5,
        ).json()

        return next(
            target
            for target in targets
            if (
                target.get("type") == "page"
                and "stremio.com"
                in target.get("url", "")
            )
        )

    @staticmethod
    def parse_frame_rate(value):

        if not value or value == "0/0":

            return None

        return round(
            float(Fraction(value)),
            3,
        )
