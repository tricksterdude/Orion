from app.providers.base import MediaProvider


class ProviderManager:

    def __init__(self):

        self.providers: list[MediaProvider] = []

    def register(self, provider: MediaProvider):

        self.providers.append(provider)

    def available(self):

        return [
            provider
            for provider in self.providers
            if provider.is_available()
        ]

    def current(self):

        providers = self.available()

        if not providers:
            return None

        return providers[0]