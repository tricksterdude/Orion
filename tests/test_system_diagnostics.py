import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

from app.system_diagnostics import SystemDiagnostics


print("=" * 60)
print("ORION SYSTEM DIAGNOSTICS TEST")
print("=" * 60)
print()


class FakeProcess:

    def __init__(self, process_id, parent_id, command):

        self.info = {
            "pid": process_id,
            "ppid": parent_id,
            "name": "pythonw.exe",
            "cmdline": command,
        }


class FakeStremio:

    def __init__(self, running=False, ready=False, installed=True):

        self.running = running
        self.ready = ready
        self.executable = SimpleNamespace(
            is_file=lambda: installed
        )

    def is_running(self):

        return self.running

    def status(self):

        return {
            "ready": self.ready,
        }


class FakeDisplay:

    def current_mode(self):

        return SimpleNamespace(
            width=3840,
            height=2160,
            refresh=120,
        )


class CommandRunner:

    def __init__(self, failures=None):

        self.failures = set(failures or [])
        self.calls = []

    def __call__(self, command, timeout):

        self.calls.append((command, timeout))

        name = "ffprobe" if "-version" in command else "docker"

        return subprocess.CompletedProcess(
            command,
            1 if name in self.failures else 0,
            stdout="available",
            stderr="not available",
        )


def write_config(root, filename, data):

    config_directory = root / "config"
    config_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with (
        config_directory / filename
    ).open("w", encoding="utf-8") as file:

        json.dump(data, file)


def project_root():

    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)

    write_config(
        root,
        "settings.json",
        {"application": "Orion"},
    )
    write_config(
        root,
        "services.json",
        {"services": []},
    )
    write_config(
        root,
        "providers.json",
        {"providers": []},
    )

    return temporary, root


def build_diagnostics(
    root,
    command_runner=None,
    processes=None,
    stremio=None,
    clock=None,
):

    return SystemDiagnostics(
        project_root=root,
        docker_resolver=lambda: "docker.exe",
        ffprobe_resolver=lambda: "ffprobe.exe",
        display_factory=FakeDisplay,
        command_runner=command_runner or CommandRunner(),
        process_iter=(
            lambda attributes: processes
            if processes is not None
            else [
                FakeProcess(
                    100,
                    50,
                    ["pythonw.exe", "background.py"],
                ),
                FakeProcess(
                    101,
                    100,
                    ["pythonw.exe", "background.py"],
                ),
            ]
        ),
        stremio_controller=(
            stremio or FakeStremio()
        ),
        clock=clock,
    )


temporary, root = project_root()

try:

    services = [
        {
            "name": "AIOStreams",
            "healthy": True,
        },
        {
            "name": "UsenetStreamer",
            "healthy": True,
        },
    ]

    diagnostics = build_diagnostics(root)
    snapshot = diagnostics.run(
        services=services
    )

    assert snapshot["status"] == "healthy"
    assert snapshot["label"] == "Healthy"
    assert snapshot["counts"] == {
        "healthy": 7,
        "warning": 0,
        "action_required": 0,
    }
    assert [
        check["id"]
        for check in snapshot["checks"]
    ] == [
        "configuration",
        "docker",
        "ffprobe",
        "display",
        "single_instance",
        "stremio",
        "services",
    ]

    print("✓ Healthy system produces a healthy summary")

    child_process_snapshot = diagnostics.run(
        services=services,
        force=True,
    )

    instance_check = next(
        check
        for check in child_process_snapshot["checks"]
        if check["id"] == "single_instance"
    )

    assert instance_check["status"] == "healthy"

    print("✓ Python launcher child is not counted twice")

    duplicate_diagnostics = build_diagnostics(
        root,
        processes=[
            FakeProcess(
                100,
                50,
                ["pythonw.exe", "background.py"],
            ),
            FakeProcess(
                200,
                60,
                ["pythonw.exe", "background.py"],
            ),
        ],
    )

    duplicate_snapshot = duplicate_diagnostics.run(
        services=services
    )

    assert duplicate_snapshot["status"] == "action_required"
    assert any(
        check["id"] == "single_instance"
        and check["status"] == "action_required"
        for check in duplicate_snapshot["checks"]
    )

    print("✓ Independent duplicate Orion runtimes are detected")

    failing_runner = CommandRunner(
        failures={"docker", "ffprobe"}
    )
    dependency_diagnostics = build_diagnostics(
        root,
        command_runner=failing_runner,
    )

    dependency_snapshot = dependency_diagnostics.run(
        services=services
    )

    assert dependency_snapshot["counts"][
        "action_required"
    ] == 2

    print("✓ Missing Docker and FFprobe require action")

    offline_snapshot = diagnostics.run(
        services=[
            {"name": "AIOStreams", "healthy": False},
        ],
        force=True,
    )

    service_check = next(
        check
        for check in offline_snapshot["checks"]
        if check["id"] == "services"
    )

    assert service_check["status"] == "warning"
    assert "0 of 1" in service_check["summary"]

    print("✓ Offline configured services produce a warning")

    broken_stremio = build_diagnostics(
        root,
        stremio=FakeStremio(
            running=True,
            ready=False,
        ),
    )

    broken_stremio_snapshot = broken_stremio.run(
        services=services
    )

    assert any(
        check["id"] == "stremio"
        and check["status"] == "action_required"
        for check in broken_stremio_snapshot["checks"]
    )

    print("✓ Stremio opened without detection is identified")

    now = [100.0]
    cache_runner = CommandRunner()
    cached_diagnostics = build_diagnostics(
        root,
        command_runner=cache_runner,
        clock=lambda: now[0],
    )

    first = cached_diagnostics.run(services=services)
    second = cached_diagnostics.run(
        services=[{"name": "Offline", "healthy": False}]
    )

    assert first == second
    assert len(cache_runner.calls) == 2

    cached_diagnostics.run(
        services=services,
        force=True,
    )

    assert len(cache_runner.calls) == 4

    print("✓ Checks are cached briefly and can be refreshed")

    write_config(
        root,
        "services.json",
        {
            "services": [
                {
                    "name": "Invalid service",
                    "container": "invalid",
                    "port": 0,
                    "url": "http://localhost",
                }
            ]
        },
    )

    invalid_config_diagnostics = build_diagnostics(root)
    invalid_config_snapshot = (
        invalid_config_diagnostics.run(
            services=services
        )
    )

    assert any(
        check["id"] == "configuration"
        and check["status"] == "action_required"
        for check in invalid_config_snapshot["checks"]
    )

    print("✓ Invalid configuration structure requires action")

    report_snapshot = dict(snapshot)
    report_snapshot["checks"] = [
        dict(check)
        for check in snapshot["checks"]
    ]
    report_snapshot["checks"][0]["summary"] = (
        "api_key=very-secret-token "
        "https://private.example/stream "
        r"C:\Users\alice\Orion"
    )

    report = diagnostics.report(report_snapshot)

    assert "very-secret-token" not in report
    assert "private.example" not in report
    assert "alice" not in report
    assert "[redacted]" in report
    assert "playback history are excluded" in report

    print("✓ Safe report redacts secrets, URLs and account paths")

finally:

    temporary.cleanup()

print()
print("✓ Orion system diagnostics test passed")
