import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from app.local_configuration import local_configuration


class SpatialAudioControlError(RuntimeError):
    pass


class SoundVolumeTools:

    VIEW_RELATIVE_PATH = (
        Path("Orion")
        / "tools"
        / "SoundVolumeView"
        / "SoundVolumeView.exe"
    )
    COMMAND_RELATIVE_PATH = (
        Path("Orion")
        / "tools"
        / "SoundVolumeCommandLine"
        / "svcl.exe"
    )

    def __init__(
        self,
        view_path=None,
        command_path=None,
        runner=None,
        sleeper=None,
    ):

        local_app_data = os.environ.get(
            "LOCALAPPDATA",
            "",
        )
        local_root = Path(local_app_data) if local_app_data else None

        self.view_path = Path(
            view_path
            or (
                local_root / self.VIEW_RELATIVE_PATH
                if local_root
                else shutil.which("SoundVolumeView.exe")
                or "SoundVolumeView.exe"
            )
        )
        self.command_path = Path(
            command_path
            or (
                local_root / self.COMMAND_RELATIVE_PATH
                if local_root
                else shutil.which("svcl.exe")
                or "svcl.exe"
            )
        )
        self.runner = runner or subprocess.run
        self.sleeper = sleeper or time.sleep

    def available(self):

        return (
            self.view_path.is_file()
            and self.command_path.is_file()
        )

    @staticmethod
    def _creation_flags():

        return getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

    def _run(self, arguments, timeout=10):

        try:

            return self.runner(
                [str(argument) for argument in arguments],
                check=False,
                capture_output=True,
                timeout=timeout,
                creationflags=self._creation_flags(),
            )

        except (OSError, subprocess.SubprocessError) as error:

            raise SpatialAudioControlError(
                "The SoundVolume helper could not be started."
            ) from error

    @staticmethod
    def _read_export(path):

        content = Path(path).read_bytes()

        if content.startswith((b"\xff\xfe", b"\xfe\xff")):

            text = content.decode("utf-16")

        else:

            text = content.decode("utf-8-sig")

        document = json.loads(text)

        if not isinstance(document, list):

            raise SpatialAudioControlError(
                "SoundVolume returned an invalid device inventory."
            )

        return document

    def _inventory(self):

        if not self.available():

            raise SpatialAudioControlError(
                "Install SoundVolumeView and SoundVolumeCommandLine "
                "before enabling automatic spatial audio."
            )

        descriptor, report_name = tempfile.mkstemp(
            prefix="orion-audio-",
            suffix=".json",
        )
        os.close(descriptor)
        report = Path(report_name)
        report.unlink(missing_ok=True)

        try:

            completed = self._run(
                [
                    self.view_path,
                    "/sjson",
                    report,
                ]
            )

            if completed.returncode != 0 or not report.is_file():

                raise SpatialAudioControlError(
                    "SoundVolume could not inspect the default audio output."
                )

            rows = self._read_export(report)

        except (OSError, UnicodeError, ValueError) as error:

            raise SpatialAudioControlError(
                "SoundVolume returned an invalid device inventory."
            ) from error

        finally:

            report.unlink(missing_ok=True)

        return rows

    @staticmethod
    def _endpoint(row):

        device_id = str(
            row.get("Command-Line Friendly ID") or ""
        ).strip()
        spatial_guid = str(
            row.get("Spatial Guid") or ""
        ).strip().upper()

        if not device_id:

            raise SpatialAudioControlError(
                "An audio output has no safe command identifier."
            )

        return {
            "name": str(row.get("Name") or "").strip(),
            "device_id": device_id,
            "spatial_guid": spatial_guid,
        }

    def default_multimedia_endpoint(self):

        endpoints = [
            row
            for row in self._inventory()
            if (
                isinstance(row, dict)
                and row.get("Type") == "Device"
                and row.get("Direction") == "Render"
                and row.get("Default Multimedia") == "Render"
                and row.get("Device State") == "Active"
            )
        ]

        if len(endpoints) != 1:

            raise SpatialAudioControlError(
                "Windows did not identify one active default multimedia output."
            )

        return self._endpoint(endpoints[0])

    def endpoint(self, device_id):

        requested = str(device_id or "").strip()
        endpoints = [
            row
            for row in self._inventory()
            if (
                isinstance(row, dict)
                and row.get("Type") == "Device"
                and row.get("Direction") == "Render"
                and str(
                    row.get("Command-Line Friendly ID") or ""
                ).strip()
                == requested
            )
        ]

        if len(endpoints) != 1:

            raise SpatialAudioControlError(
                "The saved audio output is no longer available."
            )

        return self._endpoint(endpoints[0])

    def set_spatial(self, device_id, spatial_guid):

        completed = self._run(
            [
                self.command_path,
                "/SetSpatial",
                device_id,
                spatial_guid,
            ]
        )

        return completed.returncode == 0

    def wait_for_guid(
        self,
        expected_guid,
        device_id=None,
        attempts=10,
        delay=0.5,
    ):

        expected = str(expected_guid or "").strip().upper()

        for _ in range(attempts):

            try:

                current = (
                    self.endpoint(device_id)
                    if device_id
                    else self.default_multimedia_endpoint()
                )

                if current["spatial_guid"] == expected:

                    return True

            except SpatialAudioControlError:

                pass

            self.sleeper(delay)

        return False


class SpatialAudioController:

    CHECKPOINT_VERSION = 1
    GUIDED = "guided"
    AUTOMATIC = "automatic"
    FORMAT_GUIDS = {
        "Dolby Atmos": "{A289735D-FA3E-4E35-9D7D-B6F896ACB2E7}",
        "DTS:X": "{10201B4A-3322-4967-BF40-2CAA9BAFCA44}",
    }

    def __init__(
        self,
        configuration=None,
        tools=None,
        checkpoint_path="data/audio_spatial_recovery.json",
    ):

        self.configuration = configuration or local_configuration
        self.tools = tools or SoundVolumeTools()
        self.checkpoint_path = Path(checkpoint_path)
        self._lock = threading.RLock()

    def mode(self):

        try:

            audio = self.configuration.read("media").get(
                "audio",
                {},
            )

            return str(
                audio.get("spatial_control") or self.GUIDED
            ).strip()

        except Exception:

            return self.GUIDED

    def status(self):

        return {
            "mode": self.mode(),
            "helpers_available": self.tools.available(),
            "checkpoint_pending": self.checkpoint_path.is_file(),
        }

    @classmethod
    def target_for(cls, request):

        immersive_audio = str(
            getattr(request, "immersive_audio", None) or ""
        ).strip()

        return cls.FORMAT_GUIDS.get(immersive_audio)

    @staticmethod
    def _normalise_guid(value):

        return str(value or "").strip().upper()

    def _write_checkpoint(self, endpoint, target_guid):

        self.checkpoint_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        temporary = self.checkpoint_path.with_name(
            f"{self.checkpoint_path.name}.tmp"
        )
        document = {
            "version": self.CHECKPOINT_VERSION,
            "saved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "device_id": endpoint["device_id"],
            "device_name": endpoint.get("name"),
            "previous_guid": endpoint.get("spatial_guid") or "",
            "target_guid": target_guid,
        }

        try:

            temporary.write_text(
                json.dumps(document, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.checkpoint_path)

        except OSError as error:

            temporary.unlink(missing_ok=True)

            raise SpatialAudioControlError(
                "Orion could not save the spatial-audio recovery checkpoint."
            ) from error

    def _read_checkpoint(self):

        try:

            document = json.loads(
                self.checkpoint_path.read_text(
                    encoding="utf-8-sig"
                )
            )

        except (OSError, ValueError, UnicodeError) as error:

            raise SpatialAudioControlError(
                "The spatial-audio recovery checkpoint is invalid."
            ) from error

        if (
            not isinstance(document, dict)
            or document.get("version") != self.CHECKPOINT_VERSION
            or not str(document.get("device_id") or "").strip()
        ):

            raise SpatialAudioControlError(
                "The spatial-audio recovery checkpoint is invalid."
            )

        return document

    def _clear_checkpoint(self):

        try:

            self.checkpoint_path.unlink(missing_ok=True)

            return True

        except OSError:

            return False

    def begin(self, request):

        target = self.target_for(request)

        if self.mode() != self.AUTOMATIC:

            return {
                "status": "guided",
                "changed": False,
                "message": "Automatic spatial-audio switching is disabled.",
            }

        if target is None:

            return {
                "status": "not_required",
                "changed": False,
                "message": "The stream does not require an immersive format switch.",
            }

        with self._lock:

            if self.checkpoint_path.exists():

                return {
                    "status": "failed",
                    "changed": False,
                    "message": (
                        "A previous spatial-audio recovery checkpoint is pending."
                    ),
                }

            try:

                endpoint = self.tools.default_multimedia_endpoint()
                current = self._normalise_guid(
                    endpoint.get("spatial_guid")
                )
                target = self._normalise_guid(target)

                if current == target:

                    return {
                        "status": "current",
                        "changed": False,
                        "target_guid": target,
                        "device_name": endpoint.get("name"),
                        "message": "The required spatial format is already selected.",
                    }

                self._write_checkpoint(endpoint, target)

                if (
                    not self.tools.set_spatial(
                        endpoint["device_id"],
                        target,
                    )
                    or not self.tools.wait_for_guid(
                        target,
                        endpoint["device_id"],
                    )
                ):

                    restored = self.restore()

                    return {
                        "status": "failed",
                        "changed": False,
                        "restored": restored,
                        "message": (
                            "Windows did not confirm the requested spatial format."
                        ),
                    }

                return {
                    "status": "switched",
                    "changed": True,
                    "target_guid": target,
                    "device_name": endpoint.get("name"),
                    "message": "Windows spatial audio was selected for this stream.",
                }

            except SpatialAudioControlError as error:

                return {
                    "status": "failed",
                    "changed": False,
                    "message": str(error),
                }

    def restore(self):

        with self._lock:

            if not self.checkpoint_path.exists():

                return True

            try:

                checkpoint = self._read_checkpoint()
                previous = self._normalise_guid(
                    checkpoint.get("previous_guid")
                )

                if not self.tools.set_spatial(
                    checkpoint["device_id"],
                    previous,
                ):

                    return False

                if not self.tools.wait_for_guid(
                    previous,
                    checkpoint["device_id"],
                ):

                    return False

                return self._clear_checkpoint()

            except SpatialAudioControlError:

                return False

    def recover_pending(self):

        if not self.checkpoint_path.exists():

            return {
                "status": "none",
                "message": None,
            }

        if self.restore():

            return {
                "status": "restored",
                "message": (
                    "Orion restored the spatial-audio format from an "
                    "interrupted playback session."
                ),
            }

        return {
            "status": "failed",
            "message": (
                "Orion could not restore the saved spatial-audio format. "
                "Automatic audio switching is disabled until this is resolved."
            ),
        }
