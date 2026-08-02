from app.banner import show_banner
from app.orion import Orion


def main():
    show_banner()

    app = Orion()

    app.start()


if __name__ == "__main__":
    main()