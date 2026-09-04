import base64
import json
import subprocess
import zlib
from urllib.parse import unquote, urlparse

import requests
import websocket

from app.ffprobe_cli import ffprobe_executable
from app.technical.ffprobe_metadata import (
    FFPROBE_ENTRIES,
    analyse_ffprobe_document,
    parse_frame_rate,
)


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
                "-show_entries",
                FFPROBE_ENTRIES,
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

        filename = (
            selected.get("filename")
            or ""
        )

        return analyse_ffprobe_document(
            data,
            filename=filename,
            source_host=selected.get("source_host"),
        )

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

        return parse_frame_rate(value)
