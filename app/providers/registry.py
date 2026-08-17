from app.providers.base import MediaProvider


class ProviderRegistry:

    def __init__(self):

        self._providers: dict[str, MediaProvider] = {}

    def register(self, provider: MediaProvider):

        self._providers[provider.name] = provider

    def get(self, name: str):

        return self._providers.get(name)

    def all(self):

        return list(self._providers.values())

    def available(self):

        return [
            provider
            for provider in self._providers.values()
            if provider.is_available()
        ]