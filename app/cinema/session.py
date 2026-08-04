from app.cinema.engine import CinemaEngine


class CinemaSession:

    def __init__(self):

        self.engine = CinemaEngine()

    def begin(self, fps):

        result = self.engine.analyse(fps)

        print()

        print("=" * 60)
        print("           ORION CINEMA SESSION")
        print("=" * 60)

        print()

        print(f"Movie FPS : {fps}")

        print()

        print(
            "Current : "
            f"{result['current']['refresh']} Hz"
        )

        print(
            "Target  : "
            f"{result['target']['refresh']} Hz"
        )

        print()

        if result["supported"]:

            print("✓ Ready to switch.")

        else:

            print("✗ Unsupported mode.")

        return result