from app.providers.loader import ProviderLoader


def main():

    print()
    print("=" * 60)
    print("PROVIDER LOADER")
    print("=" * 60)
    print()

    loader = ProviderLoader()

    providers = loader.load()

    print()
    print(f"Loaded {len(providers)} provider(s)")


if __name__ == "__main__":

    main()