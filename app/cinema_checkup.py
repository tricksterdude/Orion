import copy
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path


class CinemaCheckupError(RuntimeError):
    pass


class CinemaCheckup:

    VERSION = 1
    STATUS_LABELS = {
        "healthy": "Ready",
        "warning": "Ready with notes",
        "action_required": "Needs attention",
    }
    CATEGORIES = {
        "configuration": "Foundation",
        "docker": "Foundation",
        "ffprobe": "Playback",
        "display": "Picture",
        "audio_output": "Audio",
        "single_instance": "Foundation",
        "stremio": "Playback",
        "services": "Services",
    }

    def __init__(
        self,
        diagnostics,
        setup_profile,
        display,
        display_recovery,
        spatial_audio,
        history,
        path="data/cinema_checkup.json",
    ):

        self.diagnostics = diagnostics
        self.setup_profile = setup_profile
        self.display = display
        self.display_recovery = display_recovery
        self.spatial_audio = spatial_audio
        self.history = history
        self.path = Path(path)
        self._lock = threading.Lock()

    @staticmethod
    def _check(
        identifier,
        category,
        name,
        status,
        summary,
        guidance,
        detail=None,
    ):

        return {
            "id": identifier,
            "category": category,
            "name": name,
            "status": status,
            "label": CinemaCheckup.STATUS_LABELS[status],
            "summary": summary,
            "guidance": guidance,
            "detail": detail,
        }

    def _profile_check(self, profile):

        if not self.setup_profile.completed():
            return self._check(
                "profile",
                "Foundation",
                "System setup",
                "warning",
                "The local system profile has not been confirmed yet.",
                "Open Setup, review the detected values, and confirm them once.",
            )

        return self._check(
            "profile",
            "Foundation",
            "System setup",
            "healthy",
            "The local system profile is confirmed.",
            "No action is required.",
            (
                f"{len(profile['providers'])} playback provider(s) and "
                f"{len(profile['services'])} service(s) are configured."
            ),
        )

    def _baseline_check(self, profile):

        try:
            mode = self.display.current_mode()
        except Exception:
            mode = None

        if mode is None:
            return self._check(
                "desktop_baseline",
                "Picture",
                "Desktop restoration baseline",
                "action_required",
                "Orion could not read the current Windows display mode.",
                "Confirm the television is connected and restart Orion.",
            )

        display = profile["media"]["display"]
        expected_resolution = str(display["resolution"])
        current_resolution = f"{mode.width}x{mode.height}"
        expected_refresh = float(display["desktop_refresh_rate"])
        current_refresh = float(mode.refresh)
        matches = (
            current_resolution == expected_resolution
            and abs(current_refresh - expected_refresh) <= 1.0
        )
        detail = (
            f"Current: {current_resolution} at {mode.refresh} Hz. "
            f"Configured desktop: {expected_resolution} at "
            f"{display['desktop_refresh_rate']} Hz."
        )

        if not matches:
            return self._check(
                "desktop_baseline",
                "Picture",
                "Desktop restoration baseline",
                "warning",
                "The current display mode differs from Orion's desktop baseline.",
                (
                    "When no video is playing, confirm the normal desktop "
                    "mode in Setup before testing playback."
                ),
                detail,
            )

        return self._check(
            "desktop_baseline",
            "Picture",
            "Desktop restoration baseline",
            "healthy",
            "The current display matches Orion's restoration baseline.",
            "No action is required.",
            detail,
        )

    def _recovery_check(self, profile):

        display_error = False

        try:
            display_pending = bool(
                self.display_recovery.has_saved_mode()
            )
        except Exception:
            display_pending = False
            display_error = True

        audio_error = False

        try:
            audio = self.spatial_audio.status()
        except Exception:
            audio = {
                "mode": "unknown",
                "helpers_available": False,
                "checkpoint_pending": False,
            }
            audio_error = True

        if display_error or audio_error:
            unavailable = []

            if display_error:
                unavailable.append("display recovery")

            if audio_error:
                unavailable.append("spatial-audio recovery")

            return self._check(
                "recovery",
                "Safety",
                "Recovery checkpoints",
                "action_required",
                "Orion could not verify all recovery checkpoints.",
                "Restart Orion and run Cinema Checkup again.",
                "Unavailable: " + ", ".join(unavailable) + ".",
            )

        audio_pending = bool(
            audio.get("checkpoint_pending")
        )

        if display_pending or audio_pending:
            pending = []

            if display_pending:
                pending.append("display")

            if audio_pending:
                pending.append("spatial audio")

            return self._check(
                "recovery",
                "Safety",
                "Recovery checkpoints",
                "action_required",
                "An unfinished cinema recovery checkpoint is present.",
                (
                    "Restart Orion and confirm the desktop and Windows "
                    "spatial format are restored before playback."
                ),
                "Pending: " + ", ".join(pending) + ".",
            )

        spatial_mode = profile["media"]["audio"].get(
            "spatial_control",
            "guided",
        )

        if (
            spatial_mode == "automatic"
            and not audio.get("helpers_available")
        ):
            return self._check(
                "recovery",
                "Safety",
                "Recovery checkpoints",
                "action_required",
                "Automatic spatial audio is enabled but its helpers are unavailable.",
                (
                    "Install the configured SoundVolume helpers or change "
                    "spatial-audio switching to Guided in Setup."
                ),
            )

        return self._check(
            "recovery",
            "Safety",
            "Recovery checkpoints",
            "healthy",
            "No unfinished display or spatial-audio recovery is pending.",
            "No action is required.",
            (
                "Spatial audio: "
                + (
                    "automatic switching ready"
                    if spatial_mode == "automatic"
                    else "guided mode"
                )
                + "."
            ),
        )

    def _playback_evidence_check(self):

        try:
            sessions = self.history.read(limit=1)
        except Exception:
            sessions = []

        if not sessions:
            return self._check(
                "playback_evidence",
                "Proof",
                "Recent playback recovery",
                "warning",
                "No completed playback session is available to verify yet.",
                (
                    "Play and stop one title, then run Cinema Checkup "
                    "again to verify the complete recovery path."
                ),
            )

        session = sessions[0]
        playback = session.get("playback") or {}
        display_restored = session.get("display_restored")
        audio_restored = session.get("audio_restored")

        if display_restored is not True or audio_restored is False:
            failed = [
                "display"
                if display_restored is not True
                else None,
                "spatial audio"
                if audio_restored is False
                else None,
            ]
            failed = [item for item in failed if item]

            return self._check(
                "playback_evidence",
                "Proof",
                "Recent playback recovery",
                "action_required",
                "The most recent playback did not confirm full recovery.",
                (
                    "Restart Orion, restore the affected setting, and "
                    "review Playback History before trying another title."
                ),
                "Not confirmed: " + ", ".join(failed) + ".",
            )

        evidence = [
            str(playback.get("source") or "Unknown source"),
        ]

        if playback.get("fps") is not None:
            evidence.append(f"{playback['fps']} fps")

        audio = (
            playback.get("audio_profile")
            or playback.get("audio_codec")
        )

        if audio:
            evidence.append(str(audio))

        return self._check(
            "playback_evidence",
            "Proof",
            "Recent playback recovery",
            "healthy",
            "The most recent playback completed with recovery confirmed.",
            "No action is required.",
            " · ".join(evidence),
        )

    @staticmethod
    def _diagnostic_checks(snapshot):

        checks = []

        for source in snapshot.get("checks", []):
            check = copy.deepcopy(source)
            check["category"] = CinemaCheckup.CATEGORIES.get(
                check.get("id"),
                "Foundation",
            )
            status = check.get("status")

            if status in CinemaCheckup.STATUS_LABELS:
                check["label"] = CinemaCheckup.STATUS_LABELS[
                    status
                ]

            checks.append(check)

        return checks

    @classmethod
    def _summary(cls, checks):

        counts = {
            status: sum(
                1
                for check in checks
                if check.get("status") == status
            )
            for status in cls.STATUS_LABELS
        }

        if counts["action_required"]:
            status = "action_required"
        elif counts["warning"]:
            status = "warning"
        else:
            status = "healthy"

        return status, counts

    def _write(self, snapshot):

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        try:
            temporary.write_text(
                json.dumps(
                    snapshot,
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.path)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

            raise CinemaCheckupError(
                "Orion completed the checkup but could not save its result."
            ) from error

    def run(self, services=None, playback_active=False):

        if playback_active:
            raise CinemaCheckupError(
                "Cinema Checkup cannot run during playback. Stop the title "
                "and wait for Orion to restore the desktop first."
            )

        if not self._lock.acquire(blocking=False):
            raise CinemaCheckupError(
                "Cinema Checkup is already running."
            )

        try:
            try:
                profile = self.setup_profile.snapshot()
            except Exception as error:
                raise CinemaCheckupError(
                    "Orion could not read the local system profile."
                ) from error

            try:
                diagnostics = self.diagnostics.run(
                    services=services,
                    force=True,
                )
            except Exception as error:
                raise CinemaCheckupError(
                    "Orion could not complete the system checks."
                ) from error

            checks = [self._profile_check(profile)]
            checks.extend(
                self._diagnostic_checks(diagnostics)
            )
            checks.extend(
                [
                    self._baseline_check(profile),
                    self._recovery_check(profile),
                    self._playback_evidence_check(),
                ]
            )
            status, counts = self._summary(checks)
            snapshot = {
                "version": self.VERSION,
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(timespec="seconds"),
                "status": status,
                "label": self.STATUS_LABELS[status],
                "counts": counts,
                "checks": checks,
            }
            self._write(snapshot)
            return copy.deepcopy(snapshot)
        finally:
            self._lock.release()

    def latest(self):

        try:
            document = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError, TypeError):
            return None

        if (
            not isinstance(document, dict)
            or document.get("version") != self.VERSION
            or document.get("status") not in self.STATUS_LABELS
            or not isinstance(document.get("checks"), list)
        ):
            return None

        return copy.deepcopy(document)
