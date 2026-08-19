import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.display.adapter import DisplayAdapter
from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher


class DisplayRestore:

    CHECKPOINT_VERSION = 1

    def __init__(
        self,
        checkpoint_path="data/display_recovery.json",
        adapter=None,
        switcher=None,
        desktop_refresh=None,
    ):

        self.checkpoint_path = Path(
            checkpoint_path
        )

        self.adapter = (
            adapter
            or DisplayAdapter()
        )

        self.switcher = (
            switcher
            or DisplaySwitcher()
        )

        if (
            desktop_refresh is not None
            and (
                isinstance(desktop_refresh, bool)
                or not isinstance(
                    desktop_refresh,
                    int,
                )
                or desktop_refresh <= 0
            )
        ):

            raise ValueError(
                "Desktop refresh rate must be a "
                "positive integer."
            )

        self.desktop_refresh = desktop_refresh

        self.original: DisplayMode | None = None
        self._lock = threading.RLock()

    @staticmethod
    def _mode_document(mode):

        return {
            "width": mode.width,
            "height": mode.height,
            "refresh": mode.refresh,
            "bits": mode.bits,
        }

    @staticmethod
    def _mode_from_document(document):

        if not isinstance(document, dict):

            raise ValueError(
                "Display recovery mode is invalid."
            )

        values = {}

        for field in (
            "width",
            "height",
            "refresh",
            "bits",
        ):

            value = document.get(field)

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):

                raise ValueError(
                    "Display recovery mode is invalid."
                )

            values[field] = value

        return DisplayMode(**values)

    def _write_checkpoint(self, mode):

        self.checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.checkpoint_path.with_name(
            f"{self.checkpoint_path.name}.tmp"
        )

        document = {
            "version": self.CHECKPOINT_VERSION,
            "saved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "mode": self._mode_document(mode),
        }

        try:

            with temporary_path.open(
                "w",
                encoding="utf-8",
            ) as checkpoint_file:

                json.dump(
                    document,
                    checkpoint_file,
                    indent=2,
                )

                checkpoint_file.write("\n")

            os.replace(
                temporary_path,
                self.checkpoint_path,
            )

        except OSError:

            try:

                temporary_path.unlink(
                    missing_ok=True
                )

            except OSError:

                pass

            raise

    def _read_checkpoint(self):

        document = json.loads(
            self.checkpoint_path.read_text(
                encoding="utf-8"
            )
        )

        if (
            not isinstance(document, dict)
            or document.get("version")
            != self.CHECKPOINT_VERSION
        ):

            raise ValueError(
                "Display recovery checkpoint is invalid."
            )

        mode = self._mode_from_document(
            document.get("mode")
        )

        return mode, document.get("saved_at")

    def _clear_checkpoint(self):

        try:

            self.checkpoint_path.unlink(
                missing_ok=True
            )

            return True

        except OSError:

            return False

    @staticmethod
    def _mode_label(mode):

        return (
            f"{mode.width}x{mode.height} "
            f"at {mode.refresh} Hz"
        )

    def save(self):

        with self._lock:

            if self.checkpoint_path.exists():

                return False

            try:

                current = self.adapter.current_mode()

                if current is None:

                    return False

                if self.desktop_refresh is None:

                    original = current

                else:

                    original = DisplayMode(
                        width=current.width,
                        height=current.height,
                        refresh=(
                            self.desktop_refresh
                        ),
                        bits=current.bits,
                    )

                    if not self.switcher.can_switch(
                        original
                    ):

                        return False

                self._write_checkpoint(original)

            except Exception:

                return False

            self.original = original

            return True

    def has_saved_mode(self) -> bool:

        return (
            self.original is not None
            or self.checkpoint_path.exists()
        )

    def original_mode(self):

        return self.original

    def restore(self) -> bool:

        with self._lock:

            target = self.original

            if target is None:

                try:

                    target, _ = self._read_checkpoint()

                except Exception:

                    return False

            try:

                current = self.adapter.current_mode()

                restored = (
                    current == target
                    or self.switcher.switch(target)
                )

            except Exception:

                return False

            if restored:

                self._clear_checkpoint()
                self.original = None

            return restored

    def recover_pending(self):

        with self._lock:

            if not self.checkpoint_path.exists():

                return {
                    "status": "none",
                    "message": None,
                }

            try:

                target, saved_at = (
                    self._read_checkpoint()
                )

            except Exception:

                return {
                    "status": "failed",
                    "message": (
                        "Orion found an invalid display "
                        "recovery checkpoint. Automatic "
                        "display switching is disabled."
                    ),
                }

            self.original = target

            if not self.restore():

                return {
                    "status": "failed",
                    "message": (
                        "Orion detected an interrupted "
                        "cinema session but could not "
                        "restore the saved display mode "
                        f"({self._mode_label(target)}). "
                        "Automatic display switching is "
                        "disabled."
                    ),
                    "saved_at": saved_at,
                    "mode": self._mode_document(target),
                }

            return {
                "status": "restored",
                "message": (
                    "Orion recovered from an interrupted "
                    "cinema session and restored the "
                    "display to "
                    f"{self._mode_label(target)}."
                ),
                "saved_at": saved_at,
                "mode": self._mode_document(target),
            }
