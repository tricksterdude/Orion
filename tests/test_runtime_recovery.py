from types import SimpleNamespace

from app.media_manager import MediaManager
from app.recovery_status import display_recovery_status
from app.runtime import OrionRuntime


print("=" * 60)
print("RUNTIME DISPLAY RECOVERY TEST")
print("=" * 60)
print()


assert (
    MediaManager().get_desktop_refresh_rate()
    == 120
)

print("✓ Existing MediaProfile supplies 120 Hz baseline")


class FakeRestore:

    def __init__(
        self,
        save_result=True,
        recovery_result=None,
    ):

        self.save_result = save_result
        self.recovery_result = (
            recovery_result
            or {
                "status": "none",
                "message": None,
            }
        )

    def save(self):

        return self.save_result

    def recover_pending(self):

        return self.recovery_result


class FakeEngine:

    def __init__(self):

        self.started = 0
        self.cinema_calls = []

    def playback_started(self):

        self.started += 1

    def begin_cinema(self, fps):

        self.cinema_calls.append(fps)

        return {
            "switched": True,
        }


class FakeHistory:

    def __init__(self):

        self.started = 0
        self.attachments = []

    def start(self):

        self.started += 1

    def attach_metadata(
        self,
        request,
        result=None,
    ):

        self.attachments.append(
            (request, result)
        )


original_status = display_recovery_status.get()

try:

    runtime = OrionRuntime.__new__(
        OrionRuntime
    )

    runtime.restore = FakeRestore(
        recovery_result={
            "status": "restored",
            "message": "Recovered safely.",
        }
    )
    runtime.display_checkpoint_ready = True

    result = runtime.recover_display_if_needed()

    assert result["status"] == "restored"
    assert (
        display_recovery_status.get()["status"]
        == "restored"
    )
    assert runtime.display_checkpoint_ready is False

    print("✓ Startup recovery status published")

    runtime.engine = FakeEngine()
    runtime.history = FakeHistory()
    runtime.restore = FakeRestore(
        save_result=False
    )

    assert runtime.start_playback_session() is False
    assert runtime.engine.started == 1
    assert runtime.history.started == 1

    request = SimpleNamespace(
        fps=23.976,
        source="Test Provider",
    )

    assert runtime.begin_cinema_session(
        request
    ) is False
    assert runtime.engine.cinema_calls == []
    assert runtime.history.attachments == [
        (request, None)
    ]

    print(
        "✓ Metadata retained when display switch "
        "is blocked"
    )

    runtime.restore = FakeRestore(
        save_result=True
    )

    assert runtime.start_playback_session() is True
    assert runtime.begin_cinema_session(
        request
    ) is True
    assert runtime.engine.cinema_calls == [
        23.976
    ]
    assert runtime.history.attachments[-1:] == [
        (request, {"switched": True}),
    ]

    print("✓ Display switch allowed after safe checkpoint")

finally:

    display_recovery_status.set(
        original_status
    )

print()
print("✓ Runtime display recovery test passed")
