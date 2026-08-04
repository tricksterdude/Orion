import json


def main():

    with open("config/providers.json", "r") as file:

        config = json.load(file)

    print()
    print("=" * 60)
    print("PROVIDER CONFIGURATION")
    print("=" * 60)

    print()

    for provider in config["providers"]:

        print(provider)


if __name__ == "__main__":

    main()