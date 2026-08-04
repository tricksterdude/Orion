import json
import subprocess
import threading

from app.media.models import MediaState
from app.providers.base import MediaProvider


class AIOStreamsProvider(MediaProvider):

    def __init__(self):
        self._state = MediaState()
        self._process = None
        self._thread = None

    @property
    def name(self):
        return "AIOStreams"

    def is_available(self):
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return "aiostreams" in result.stdout.splitlines()

        except Exception:
            return False

    def current_media(self):
        return self._state

    def start(self):

        if self._thread is not None:
            return

        self._thread = threading.Thread(
            target=self._watch,
            daemon=True,
        )

        self._thread.start()

    def _watch(self):

        self._process = subprocess.Popen(
            [
                "docker",
                "logs",
                "--tail",
                "0",
                "-f",
                "aiostreams",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        for line in self._process.stdout:

            line = line.strip()

            if not line.startswith("{"):
                continue

            try:
                event = json.loads(line)

            except json.JSONDecodeError:
                continue

            if event.get("module") != "filterer":
                continue

            if not event.get("id"):
                continue

            if not event.get("title"):
                continue

            self._state.player = "AIOStreams"
            self._state.title = event.get("title")
            self._state.imdb_id = event.get("id")
            self._state.year = event.get("year")
            self._state.playing = True
            self._state.paused = False
            self._state.stopped = False

            print()
            print("=" * 60)
            print("AIOSTREAMS EVENT")
            print("=" * 60)
            print(f"IMDb   : {self._state.imdb_id}")
            print(f"Title  : {self._state.title}")
            print(f"Year   : {self._state.year}")
            print(f"Player : {self._state.player}")
            print()