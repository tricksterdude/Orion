import json

from app.local_configuration import providers_config_path
from app.providers.playback.aiostreams import (
    AIOStreamsPlaybackProvider,
)
from app.providers.playback.usenetstreamer import (
    UsenetStreamerPlaybackProvider,
)


class ProviderManager:

    PROVIDERS = {
        "AIOStreams": AIOStreamsPlaybackProvider,
        "UsenetStreamer": UsenetStreamerPlaybackProvider,
    }

    def __init__(
        self,
        session,
        on_playback=None,
        on_stopped=None,
        enabled_providers=None,
        provider_types=None,
    ):

        if enabled_providers is None:
            try:
                document = json.loads(
                    providers_config_path().read_text(
                        encoding="utf-8"
                    )
                )
                enabled_providers = document.get(
                    "providers",
                    [],
                )
            except (OSError, ValueError, TypeError):
                enabled_providers = []

        types = provider_types or self.PROVIDERS

        self.providers = [
            types[name](
                session,
                on_playback,
                on_stopped,
            )
            for name in enabled_providers
            if name in types
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
