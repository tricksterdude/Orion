import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class PlaybackHistory:

    def __init__(
        self,
        path="data/playback_history.jsonl",
    ):

        self.path = Path(path)
        self.current = None
        self.started_monotonic = None

    @staticmethod
    def timestamp():

        return datetime.now(
            timezone.utc
        ).isoformat(timespec="seconds")

    @staticmethod
    def display_mode(mode):

        if mode is None:

            return None

        return {
            "width": mode.width,
            "height": mode.height,
            "refresh": mode.refresh,
            "bits": mode.bits,
        }

    def start(self):

        self.started_monotonic = time.monotonic()

        self.current = {
            "session_id": str(uuid4()),
            "started_at": self.timestamp(),
            "ended_at": None,
            "duration_seconds": None,
            "playback": None,
            "cinema": None,
            "display_restored": None,
        }

    def attach_metadata(
        self,
        request,
        cinema_result,
    ):

        if self.current is None:

            self.start()

        self.current["playback"] = asdict(
            request
        )

        self.current["cinema"] = {
            "current_mode": self.display_mode(
                cinema_result.get("current")
            ),
            "target_mode": self.display_mode(
                cinema_result.get("target")
            ),
            "supported": cinema_result.get(
                "supported"
            ),
            "simulation": cinema_result.get(
                "simulation"
            ),
            "switched": cinema_result.get(
                "switched"
            ),
        }

    def finish(self, restored):

        if self.current is None:

            return False

        self.current["ended_at"] = self.timestamp()
        self.current["display_restored"] = restored

        if self.started_monotonic is not None:

            self.current["duration_seconds"] = round(
                time.monotonic()
                - self.started_monotonic,
                1,
            )

        saved = self._append(self.current)

        self.current = None
        self.started_monotonic = None

        return saved

    def _append(self, record):

        try:

            self.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with self.path.open(
                "a",
                encoding="utf-8",
            ) as history_file:

                json.dump(
                    record,
                    history_file,
                    ensure_ascii=False,
                )

                history_file.write("\n")

            return True

        except OSError as error:

            print()
            print(
                "✗ Playback history could not "
                "be saved:"
            )
            print(error)
            print()

            return False