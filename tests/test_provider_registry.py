from app.providers.registry import ProviderRegistry


def main():

    registry = ProviderRegistry()

    print()
    print("=" * 60)
    print("PROVIDER REGISTRY")
    print("=" * 60)

    print()

    print("Registered providers:")

    print(registry.all())

    print()

    print("Available providers:")

    print(registry.available())


if __name__ == "__main__":

    main()