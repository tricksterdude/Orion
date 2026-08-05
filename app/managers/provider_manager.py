from app.providers.aiostreams import AIOStreamsProvider


class ProviderManager:

    def __init__(self, session):

        self.providers = [
            AIOStreamsProvider(session)
        ]

    def start(self):

        for provider in self.providers:

            if provider.is_available():

                print(f"✓ Starting {provider.name}")

                provider.start()

    def stop(self):

        for provider in self.providers:

            provider.stop()