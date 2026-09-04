import json
import os
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.audio.spatial_processors import SpatialAudioProcessors
from app.audio.windows_output import WindowsAudioOutput
from app.receivers.manager import ReceiverManager


class PlaybackHistory:

    MAX_ENTRIES = 15

    def __init__(
        self,
        path="data/playback_history.jsonl",
        audio_output=None,
        spatial_processors=None,
        receiver_manager=None,
    ):

        self.path = Path(path)
        self.current = None
        self.started_monotonic = None
        self.audio_output = (
            audio_output or WindowsAudioOutput()
        )
        self.spatial_processors = (
            spatial_processors or SpatialAudioProcessors()
        )
        self.receiver_manager = (
            receiver_manager or ReceiverManager()
        )
        self._lock = threading.Lock()

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
            "audio_output": None,
            "audio_processing": None,
            "receiver": None,
            "cinema": None,
            "display_restored": None,
        }

    def attach_metadata(
        self,
        request,
        cinema_result=None,
    ):

        if self.current is None:

            self.start()

        self.current["playback"] = asdict(
            request
        )

        try:

            endpoint = self.audio_output.default_endpoint()
            self.current["audio_output"] = endpoint.as_dict()

        # Audio observation must never interrupt playback history.
        except Exception:

            self.current["audio_output"] = None

        try:

            self.current["audio_processing"] = (
                self.spatial_processors.recommendation(
                    getattr(
                        request,
                        "immersive_audio",
                        None,
                    )
                )
            )

        # Optional app detection must never interrupt playback.
        except Exception:

            self.current["audio_processing"] = None

        try:

            self.current["receiver"] = (
                self.receiver_manager.observe(request)
            )

        # Receiver monitoring is optional and must never delay recovery.
        except Exception:

            self.current["receiver"] = {
                "available": False,
                "error": "Receiver status was not available.",
            }

        if cinema_result is None:

            self.current["cinema"] = None
            return

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

    def read(self, limit=MAX_ENTRIES):

        try:

            limit = int(limit)

        except (
            TypeError,
            ValueError,
        ):

            limit = self.MAX_ENTRIES

        if limit <= 0:

            return []

        limit = min(
            limit,
            self.MAX_ENTRIES,
        )

        if not self.path.exists():

            return []

        try:

            records = self._read_records()

        except OSError:

            return []

        return list(
            reversed(records[-limit:])
        )

    def _read_records(self):

        if not self.path.exists():

            return []

        lines = self.path.read_text(
            encoding="utf-8"
        ).splitlines()

        records = []

        for line in lines:

            try:

                record = json.loads(line)

            except (
                json.JSONDecodeError,
                TypeError,
            ):

                continue

            if isinstance(record, dict):

                records.append(record)

        return records

    def _write_records(self, records):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.path.with_name(
            f"{self.path.name}.tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as history_file:

            for record in records:

                json.dump(
                    record,
                    history_file,
                    ensure_ascii=False,
                )

                history_file.write("\n")

        os.replace(
            temporary_path,
            self.path,
        )

    def delete(self, session_id):

        requested_id = str(
            session_id or ""
        ).strip()

        if not requested_id:

            return False

        with self._lock:

            try:

                records = self._read_records()

                remaining = [
                    record
                    for record in records
                    if str(
                        record.get("session_id")
                        or ""
                    )
                    != requested_id
                ]

                if len(remaining) == len(records):

                    return False

                self._write_records(
                    remaining[-self.MAX_ENTRIES:]
                )

                return True

            except OSError:

                return None

    def clear(self):

        with self._lock:

            try:

                records = self._read_records()

                if self.path.exists():

                    self.path.unlink()

                return len(records)

            except OSError:

                return None

    def _append(self, record):

        try:

            with self._lock:

                records = self._read_records()

                records.append(record)

                self._write_records(
                    records[-self.MAX_ENTRIES:]
                )

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
