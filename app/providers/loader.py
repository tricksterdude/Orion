import importlib
import json

from app.local_configuration import providers_config_path


class ProviderLoader:

    def __init__(self):

        self.providers = []

    def load(self):

        with providers_config_path().open(
            "r",
            encoding="utf-8",
        ) as file:

            config = json.load(file)

        for provider in config["providers"]:

            module_name = provider.lower()

            try:

                module = importlib.import_module(
                    f"app.providers.{module_name}"
                )

                self.providers.append(module)

                print(f"✓ Loaded {provider}")

            except ModuleNotFoundError:

                print(f"✗ {provider} not installed")

        return self.providers
