from app.managers.provider_manager import ProviderManager


print("=" * 60)
print("PLAYBACK PROVIDER SELECTION TEST")
print("=" * 60)
print()


class FakeProvider:

    name = "Fake"

    def __init__(
        self,
        session,
        on_playback=None,
        on_stopped=None,
    ):

        self.session = session
        self.started = False
        self.stopped = False

    def is_available(self):

        return True

    def start(self):

        self.started = True

    def stop(self):

        self.stopped = True


session = object()
manager = ProviderManager(
    session,
    enabled_providers=["Enabled", "Unknown"],
    provider_types={"Enabled": FakeProvider},
)

assert len(manager.providers) == 1
assert manager.providers[0].session is session

manager.start()
assert manager.providers[0].started

manager.stop()
assert manager.providers[0].stopped

print("✓ Only enabled, supported playback providers are started")

disabled = ProviderManager(
    session,
    enabled_providers=[],
    provider_types={"Enabled": FakeProvider},
)
assert disabled.providers == []

print("✓ Playback providers can be disabled by local profile")
print()
print("✓ Playback provider selection test passed")
