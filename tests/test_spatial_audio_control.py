import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from app.audio.spatial_control import (
    SoundVolumeTools,
    SpatialAudioController,
)


print("=" * 60)
print("SPATIAL AUDIO CONTROL TEST")
print("=" * 60)
print()


class FakeConfiguration:

    def __init__(self, mode="automatic"):

        self.mode = mode

    def read(self, kind):

        assert kind == "media"

        return {
            "audio": {
                "spatial_control": self.mode,
            }
        }


class FakeTools:

    def __init__(self, current_guid, switch_ok=True):

        self.current_guid = current_guid
        self.switch_ok = switch_ok
        self.changes = []

    def available(self):

        return True

    def default_multimedia_endpoint(self):

        return {
            "name": "2 - DENON-AVR",
            "device_id": "AMD Audio\\Device\\DENON\\Render",
            "spatial_guid": self.current_guid,
        }

    def set_spatial(self, device_id, spatial_guid):

        self.changes.append((device_id, spatial_guid))

        if self.switch_ok:

            self.current_guid = spatial_guid

        return self.switch_ok

    def wait_for_guid(self, expected_guid, device_id=None):

        return self.current_guid == expected_guid


DOLBY = SpatialAudioController.FORMAT_GUIDS["Dolby Atmos"]
DTS = SpatialAudioController.FORMAT_GUIDS["DTS:X"]
atmos = SimpleNamespace(immersive_audio="Dolby Atmos")


with TemporaryDirectory() as directory:

    checkpoint = Path(directory) / "audio_recovery.json"
    tools = FakeTools(DTS)
    controller = SpatialAudioController(
        configuration=FakeConfiguration(),
        tools=tools,
        checkpoint_path=checkpoint,
    )

    switched = controller.begin(atmos)

    assert switched["status"] == "switched"
    assert switched["changed"] is True
    assert tools.current_guid == DOLBY
    assert checkpoint.is_file()

    saved = json.loads(
        checkpoint.read_text(encoding="utf-8")
    )

    assert saved["previous_guid"] == DTS
    assert saved["target_guid"] == DOLBY

    assert controller.restore() is True
    assert tools.current_guid == DTS
    assert not checkpoint.exists()

    print("✓ Spatial format checkpointed, switched, verified and restored")

    current_tools = FakeTools(DOLBY)
    current_controller = SpatialAudioController(
        configuration=FakeConfiguration(),
        tools=current_tools,
        checkpoint_path=checkpoint,
    )

    current = current_controller.begin(atmos)

    assert current["status"] == "current"
    assert current_tools.changes == []
    assert not checkpoint.exists()

    guided_tools = FakeTools(DTS)
    guided = SpatialAudioController(
        configuration=FakeConfiguration("guided"),
        tools=guided_tools,
        checkpoint_path=checkpoint,
    ).begin(atmos)

    assert guided["status"] == "guided"
    assert guided_tools.changes == []

    print("✓ Guided mode and already-correct formats remain unchanged")

    failed_tools = FakeTools(DTS, switch_ok=False)
    failed_controller = SpatialAudioController(
        configuration=FakeConfiguration(),
        tools=failed_tools,
        checkpoint_path=checkpoint,
    )

    failed = failed_controller.begin(atmos)

    assert failed["status"] == "failed"
    assert checkpoint.is_file()
    checkpoint.unlink()

    print("✓ Failed switching retains the recovery checkpoint")

    recovery_tools = FakeTools(DOLBY)
    recovery_controller = SpatialAudioController(
        configuration=FakeConfiguration(),
        tools=recovery_tools,
        checkpoint_path=checkpoint,
    )
    recovery_controller._write_checkpoint(
        recovery_tools.default_multimedia_endpoint(),
        DOLBY,
    )
    saved = json.loads(
        checkpoint.read_text(encoding="utf-8")
    )
    saved["previous_guid"] = DTS
    checkpoint.write_text(
        json.dumps(saved),
        encoding="utf-8",
    )

    recovered = recovery_controller.recover_pending()

    assert recovered["status"] == "restored"
    assert recovery_tools.current_guid == DTS
    assert not checkpoint.exists()

    print("✓ Interrupted spatial-audio session recovered")


with TemporaryDirectory() as directory:

    root = Path(directory)
    view = root / "SoundVolumeView.exe"
    command = root / "svcl.exe"
    view.write_bytes(b"test")
    command.write_bytes(b"test")

    calls = []

    def runner(arguments, **options):

        calls.append(arguments)

        if "/sjson" in arguments:

            report = Path(
                arguments[arguments.index("/sjson") + 1]
            )
            report.write_text(
                json.dumps(
                    [
                        {
                            "Name": "2 - DENON-AVR",
                            "Type": "Device",
                            "Direction": "Render",
                            "Default Multimedia": "Render",
                            "Device State": "Active",
                            "Command-Line Friendly ID": "DENON\\Render",
                            "Spatial Guid": DTS,
                        }
                    ]
                ),
                encoding="utf-16",
            )

        return SimpleNamespace(returncode=0)

    tools = SoundVolumeTools(
        view_path=view,
        command_path=command,
        runner=runner,
        sleeper=lambda delay: None,
    )

    endpoint = tools.default_multimedia_endpoint()

    assert endpoint["name"] == "2 - DENON-AVR"
    assert endpoint["device_id"] == "DENON\\Render"
    assert endpoint["spatial_guid"] == DTS
    assert tools.set_spatial(endpoint["device_id"], DOLBY)
    assert calls[-1][1:] == [
        "/SetSpatial",
        "DENON\\Render",
        DOLBY,
    ]

    print("✓ NirSoft inventory is parsed and commands use exact endpoint IDs")

print()
print("✓ Spatial audio control test passed")
