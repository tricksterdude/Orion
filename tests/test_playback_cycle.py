from types import SimpleNamespace

from app.runtime import OrionRuntime


print("=" * 60)
print("ORION SIMULATED PLAYBACK CYCLE TEST")
print("=" * 60)
print()


events = []


class FakeRestore:

    def save(self):

        events.append("checkpoint:120")
        return True

    def restore(self):

        events.append("display:120")
        return True


class FakeEngine:

    def playback_started(self):

        events.append("playback:started")

    def begin_cinema(self, fps):

        events.append(f"display:{fps}")

        return {
            "current_refresh": 120,
            "target_refresh": 23,
            "switched": True,
        }

    def playback_stopped(self):

        events.append("playback:stopped")


class FakeHistory:

    def start(self):

        events.append("history:started")

    def attach_metadata(self, request, result=None):

        events.append(
            f"metadata:{request.source}:{request.fps}"
        )

        assert result["target_refresh"] == 23

    def finish(self, restored):

        events.append(f"history:restored:{restored}")


class FakeProviders:

    def reset(self):

        events.append("providers:reset")


runtime = OrionRuntime.__new__(OrionRuntime)
runtime.restore = FakeRestore()
runtime.engine = FakeEngine()
runtime.history = FakeHistory()
runtime.providers = FakeProviders()
runtime.display_checkpoint_ready = False
runtime.clear_playback_requests = (
    lambda: events.append("requests:cleared")
)

request = SimpleNamespace(
    source="AIOStreams",
    fps=23.976,
)

assert runtime.start_playback_session() is True
assert runtime.begin_cinema_session(request) is True
runtime.stop_playback_session()

assert events == [
    "playback:started",
    "checkpoint:120",
    "history:started",
    "display:23.976",
    "metadata:AIOStreams:23.976",
    "display:120",
    "history:restored:True",
    "playback:stopped",
    "requests:cleared",
    "providers:reset",
]

assert runtime.display_checkpoint_ready is False

print("✓ 120 Hz desktop checkpoint is saved before switching")
print("✓ AIOStreams 23.976 FPS metadata drives cinema mode")
print("✓ Playback stop restores 120 Hz and records restoration")
print("✓ Provider and playback state are reset cleanly")
print()
print("✓ Orion simulated playback cycle test passed")
