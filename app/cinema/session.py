from app.cinema.engine import CinemaEngine


class CinemaSession:

    def __init__(self):

        self.engine = CinemaEngine()

    def begin(self, fps):

        result = self.engine.analyse(fps)

        print()
        print("=" * 60)
        print("              ORION CINEMA SESSION")
        print("=" * 60)
        print()

        print(f"Movie FPS : {fps:.3f}")
        print()

        print(
            f"Current : "
            f"{result['current'].width}x"
            f"{result['current'].height} @ "
            f"{result['current'].refresh} Hz"
        )

        print(
            f"Target  : "
            f"{result['target'].width}x"
            f"{result['target'].height} @ "
            f"{result['target'].refresh} Hz"
        )

        print()

        if not result["supported"]:

            result["switched"] = False

            print("✗ Unsupported display mode.")

            return result

        if not result["simulation"]:

            result["switched"] = False

            print("✗ Windows rejected the display mode.")

            return result

        if result["current"] == result["target"]:

            result["switched"] = True

            print("✓ Display is already using the target mode.")

            return result

        result["switched"] = self.engine.activate(result)

        if result["switched"]:
            print("✓ Display switched successfully.")
        else:
            print("✗ Display switch failed.")

        return result