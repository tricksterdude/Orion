import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.display.mode import DisplayMode
from app.display.restore import DisplayRestore


print("=" * 60)
print("CRASH-SAFE DISPLAY RECOVERY TEST")
print("=" * 60)
print()


class FakeAdapter:

    def __init__(self, mode):

        self.mode = mode

    def current_mode(self):

        return self.mode


class FakeSwitcher:

    def __init__(
        self,
        succeed=True,
        supported=True,
    ):

        self.succeed = succeed
        self.supported = supported
        self.targets = []

    def can_switch(self, target):

        return self.supported

    def switch(self, target):

        self.targets.append(target)

        return self.succeed


desktop_mode = DisplayMode(
    width=3840,
    height=2160,
    refresh=120,
    bits=32,
)

cinema_mode = DisplayMode(
    width=3840,
    height=2160,
    refresh=23,
    bits=32,
)


with TemporaryDirectory() as directory:

    checkpoint = (
        Path(directory)
        / "display_recovery.json"
    )

    restore = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(desktop_mode),
        switcher=FakeSwitcher(),
    )

    assert restore.save() is True
    assert restore.has_saved_mode() is True
    assert checkpoint.is_file()
    assert not checkpoint.with_name(
        "display_recovery.json.tmp"
    ).exists()

    document = json.loads(
        checkpoint.read_text(
            encoding="utf-8"
        )
    )

    assert document["version"] == 1
    assert document["mode"] == {
        "width": 3840,
        "height": 2160,
        "refresh": 120,
        "bits": 32,
    }
    assert document["saved_at"]

    assert restore.save() is False

    print("✓ Original display mode saved atomically")
    print("✓ Existing recovery checkpoint not overwritten")

    recovery_switcher = FakeSwitcher()

    recovered = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(cinema_mode),
        switcher=recovery_switcher,
    ).recover_pending()

    assert recovered["status"] == "restored"
    assert recovered["mode"]["refresh"] == 120
    assert recovery_switcher.targets == [
        desktop_mode
    ]
    assert not checkpoint.exists()

    print("✓ Interrupted display session recovered")
    print("✓ Successful recovery checkpoint cleared")

    already_safe = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(desktop_mode),
        switcher=FakeSwitcher(),
    )

    assert already_safe.save() is True

    no_switch_needed = FakeSwitcher()

    result = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(desktop_mode),
        switcher=no_switch_needed,
    ).recover_pending()

    assert result["status"] == "restored"
    assert no_switch_needed.targets == []
    assert not checkpoint.exists()

    print("✓ Already-restored display handled safely")

    failed_restore = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(desktop_mode),
        switcher=FakeSwitcher(),
    )

    assert failed_restore.save() is True

    failed_switcher = FakeSwitcher(
        succeed=False
    )

    failed = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(cinema_mode),
        switcher=failed_switcher,
    ).recover_pending()

    assert failed["status"] == "failed"
    assert checkpoint.exists()
    assert failed_switcher.targets == [
        desktop_mode
    ]

    print("✓ Failed recovery remains available for retry")

    checkpoint.write_text(
        '{"version": 1, "mode": {"refresh": 120}}',
        encoding="utf-8",
    )

    invalid = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(cinema_mode),
        switcher=FakeSwitcher(),
    ).recover_pending()

    assert invalid["status"] == "failed"
    assert checkpoint.exists()

    print("✓ Invalid recovery checkpoint fails closed")

    checkpoint.unlink()

    configured_restore = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(cinema_mode),
        switcher=FakeSwitcher(),
        desktop_refresh=120,
    )

    assert configured_restore.save() is True

    configured_document = json.loads(
        checkpoint.read_text(
            encoding="utf-8"
        )
    )

    assert (
        configured_document["mode"]["refresh"]
        == 120
    )

    print("✓ Configured 120 Hz desktop baseline preserved")

    checkpoint.unlink()

    unsupported_restore = DisplayRestore(
        checkpoint_path=checkpoint,
        adapter=FakeAdapter(cinema_mode),
        switcher=FakeSwitcher(
            supported=False
        ),
        desktop_refresh=120,
    )

    assert unsupported_restore.save() is False
    assert not checkpoint.exists()

    print("✓ Unsupported desktop baseline fails closed")

print()
print("✓ Crash-safe display recovery test passed")
