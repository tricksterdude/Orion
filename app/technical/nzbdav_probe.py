import base64
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote


class NZBDAVProbe:

    def __init__(self):

        root = Path(__file__).resolve().parents[2]

        config_path = root / "config" / "local.json"

        if not config_path.exists():

            raise RuntimeError(
                "Missing config/local.json"
            )

        config = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )

        nzbdav = config.get("nzbdav", {})

        self.username = nzbdav.get("username")
        self.password = nzbdav.get("password")

        if not self.username or not self.password:

            raise RuntimeError(
                "Missing NZBDAV WebDAV credentials"
            )

    def probe(self, docker_url):

        url = docker_url.replace(
            "http://host.docker.internal:8500",
            "http://localhost:8500",
        )

        credentials = (
            f"{self.username}:{self.password}"
        )

        authorization = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-headers",
                (
                    "Authorization: Basic "
                    f"{authorization}\r\n"
                ),
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
                url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
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

        stream = streams[0]

        frame_rate = (
            stream.get("avg_frame_rate")
            or stream.get("r_frame_rate")
        )

        fps = self.parse_frame_rate(frame_rate)

        transfer = (
            stream.get("color_transfer")
            or ""
        ).lower()

        hdr = transfer in {
            "smpte2084",
            "arib-std-b67",
        }

        filename = unquote(
            url.rsplit("/", 1)[-1]
        )

        return {
            "url": url,
            "filename": filename,
            "fps": fps,
            "width": stream.get("width"),
            "height": stream.get("height"),
            "codec": stream.get("codec_name"),
            "color_transfer": transfer,
            "color_primaries": (
                stream.get("color_primaries")
            ),
            "hdr": hdr,
        }

    @staticmethod
    def parse_frame_rate(value):

        if not value or value == "0/0":

            return None

        return float(Fraction(value))