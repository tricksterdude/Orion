from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from app.stremio_controller import StremioController


print("=" * 60)
print("STREMIO CONTROLLER TEST")
print("=" * 60)
print()


class FakeProbe:

    def __init__(self, available=False):

        self.available = available

    def debugger_available(self):

        return self.available


with TemporaryDirectory() as temporary_directory:

    executable = (
        Path(temporary_directory)
        / "stremio-shell-ng.exe"
    )
    executable.touch()

    launches = []

    def launch(command, **options):

        launches.append((command, options))
        return SimpleNamespace()

    controller = StremioController(
        probe=FakeProbe(),
        process_iter=lambda attributes: [],
        process_launcher=launch,
        executable=executable,
    )

    status = controller.status()

    assert status["state"] == "stopped"
    assert status["can_launch"] is True

    result = controller.launch()

    assert result["ok"] is True
    assert launches[0][0] == [str(executable)]
    assert (
        "--remote-debugging-port=9222"
        in launches[0][1]["env"][
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"
        ]
    )
    assert (
        "--remote-allow-origins=*"
        in launches[0][1]["env"][
            "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"
        ]
    )

    print(
        "✓ Updated Stremio launched with compatible "
        "metadata endpoint"
    )

    running_process = SimpleNamespace(
        info={"name": "stremio-shell-ng.exe"}
    )

    running_controller = StremioController(
        probe=FakeProbe(),
        process_iter=(
            lambda attributes: [running_process]
        ),
        process_launcher=launch,
        executable=executable,
    )

    running_status = running_controller.status()

    assert (
        running_status["state"]
        == "restart_required"
    )
    assert running_controller.launch()["ok"] is False
    assert len(launches) == 1

    print("✓ Running Stremio is never terminated silently")

    ready_controller = StremioController(
        probe=FakeProbe(available=True),
        process_iter=lambda attributes: [],
        process_launcher=launch,
        executable=executable,
    )

    ready_status = ready_controller.status()

    assert ready_status["state"] == "ready"
    assert ready_status["ready"] is True

    print("✓ Active metadata endpoint detected")

    class InaccessibleExecutable:

        def is_file(self):

            raise PermissionError()

    inaccessible_controller = StremioController(
        probe=FakeProbe(),
        process_iter=lambda attributes: [],
        process_launcher=launch,
        executable=executable,
    )
    inaccessible_controller.executable = (
        InaccessibleExecutable()
    )

    inaccessible_status = (
        inaccessible_controller.status()
    )

    assert (
        inaccessible_status["state"]
        == "unavailable"
    )

    print("✓ Inaccessible install path handled safely")

print()
print("✓ Stremio controller test passed")
