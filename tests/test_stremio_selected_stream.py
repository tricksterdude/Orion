import base64
import json
import subprocess
import zlib
from fractions import Fraction
from urllib.parse import unquote, urlparse

import requests
import websocket


targets = requests.get(
    "http://127.0.0.1:9222/json",
    timeout=5,
).json()

page = next(
    target
    for target in targets
    if target.get("type") == "page"
)

socket = websocket.create_connection(
    page["webSocketDebuggerUrl"],
    timeout=5,
    suppress_origin=True,
)

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

socket.close()

location = (
    response["result"]
    ["result"]
    ["value"]
)

fragment = urlparse(location).fragment
parts = fragment.split("/")

if len(parts) < 3 or parts[1] != "player":

    raise RuntimeError(
        "Stremio is not currently playing."
    )

encoded_stream = unquote(parts[2])

padding = "=" * (
    (-len(encoded_stream)) % 4
)

compressed = base64.urlsafe_b64decode(
    encoded_stream + padding
)

stream = json.loads(
    zlib.decompress(compressed)
)

stream_url = stream.get("url")

if not stream_url:

    raise RuntimeError(
        "Selected stream has no direct URL."
    )

behavior = stream.get(
    "behaviorHints",
    {},
)

parsed_url = urlparse(stream_url)

print("=" * 60)
print("STREMIO DIRECT STREAM FFPROBE")
print("=" * 60)
print()
print(
    "Filename:",
    behavior.get("filename"),
)
print(
    "Source host:",
    parsed_url.hostname,
)
print()
print("Running FFprobe...")
print()

result = subprocess.run(
    [
        "ffprobe",
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
        stream_url,
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=60,
)

if result.returncode != 0:

    print("FFprobe failed:")
    print(result.stderr)

else:

    data = json.loads(result.stdout)

    video = data["streams"][0]

    frame_rate = (
        video.get("avg_frame_rate")
        or video.get("r_frame_rate")
    )

    fps = round(
        float(Fraction(frame_rate)),
        3,
    )

    safe_result = {
        "fps": fps,
        "codec": video.get("codec_name"),
        "width": video.get("width"),
        "height": video.get("height"),
        "colorTransfer": video.get(
            "color_transfer"
        ),
        "colorPrimaries": video.get(
            "color_primaries"
        ),
    }

    print(
        json.dumps(
            safe_result,
            indent=2,
        )
    )