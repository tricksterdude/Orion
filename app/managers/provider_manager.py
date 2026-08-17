from app.providers.playback.aiostreams import (
    AIOStreamsPlaybackProvider,
)
from app.providers.playback.usenetstreamer import (
    UsenetStreamerPlaybackProvider,
)


class ProviderManager:

    def __init__(
        self,
        session,
        on_playback=None,
    ):

        self.providers = [
            AIOStreamsPlaybackProvider(
                session
            ),
            UsenetStreamerPlaybackProvider(
                session,
                on_playback,
            ),
        ]

    def start(self):

        for provider in self.providers:

            if provider.is_available():

                print(
                    f"✓ Starting {provider.name}"
                )

                provider.start()

    def stop(self):

        for provider in self.providers:

            provider.stop()

    def reset(self):

        for provider in self.providers:

            reset = getattr(
                provider,
                "reset",
                None,
            )

            if callable(reset):

                reset()