import os


class WindowsSoundSettings:

    URI = "ms-settings:sound"

    def __init__(
        self,
        launcher=None,
        platform_name=None,
    ):

        self.platform_name = platform_name or os.name
        self.launcher = (
            launcher
            if launcher is not None
            else getattr(os, "startfile", None)
        )

    def open(self):

        if self.platform_name != "nt":

            return {
                "ok": False,
                "message": (
                    "Windows sound settings are available only on Windows."
                ),
            }

        if self.launcher is None:

            return {
                "ok": False,
                "message": (
                    "Windows could not open the sound settings page."
                ),
            }

        try:

            self.launcher(self.URI)

        except OSError:

            return {
                "ok": False,
                "message": (
                    "Windows could not open the sound settings page."
                ),
            }

        return {
            "ok": True,
            "message": (
                "Windows sound settings opened. Select the Denon output "
                "and choose Orion's recommended spatial format."
            ),
        }
