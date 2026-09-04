import base64
import json
import subprocess
from pathlib import Path
from urllib.parse import unquote

from app.ffprobe_cli import ffprobe_executable
from app.technical.ffprobe_metadata import (
    FFPROBE_ENTRIES,
    analyse_ffprobe_document,
    parse_frame_rate,
)


class NZBDAVProbe:

    def __init__(self):

        root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        config_path = (
            root
            / "config"
            / "local.json"
        )

        if not config_path.exists():

            raise RuntimeError(
                "Missing config/local.json"
            )

        config = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )

        nzbdav = config.get(
            "nzbdav",
            {},
        )

        self.username = nzbdav.get(
            "username"
        )

        self.password = nzbdav.get(
            "password"
        )

        if (
            not self.username
            or not self.password
        ):

            raise RuntimeError(
                "Missing NZBDAV WebDAV credentials"
            )

    def probe(self, docker_url):

        url = docker_url.replace(
            (
                "http://host.docker."
                "internal:8500"
            ),
            "http://localhost:8500",
        )

        credentials = (
            f"{self.username}:"
            f"{self.password}"
        )

        authorization = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        result = subprocess.run(
            [
                ffprobe_executable(),
                "-v",
                "error",
                "-headers",
                (
                    "Authorization: Basic "
                    f"{authorization}\r\n"
                ),
                "-show_entries",
                FFPROBE_ENTRIES,
                "-of",
                "json",
                url,
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

        filename = unquote(
            url.rsplit("/", 1)[-1]
        )

        return analyse_ffprobe_document(
            data,
            filename=filename,
            url=url,
        )

    @staticmethod
    def parse_frame_rate(value):

        if not value or value == "0/0":

            return None

        return parse_frame_rate(value)
