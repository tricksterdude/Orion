import subprocess


class DisplayManager:

    def get_current_resolution(self):

        try:

            output = subprocess.check_output(
                [
                    "powershell",
                    "-Command",
                    "(Get-CimInstance Win32_VideoController).CurrentHorizontalResolution"
                ],
                text=True
            )

            width = output.strip()

            output = subprocess.check_output(
                [
                    "powershell",
                    "-Command",
                    "(Get-CimInstance Win32_VideoController).CurrentVerticalResolution"
                ],
                text=True
            )

            height = output.strip()

            return f"{width} x {height}"

        except Exception:

            return "Unknown"

    def get_refresh_rate(self):

        try:

            output = subprocess.check_output(
                [
                    "powershell",
                    "-Command",
                    "(Get-CimInstance Win32_VideoController).CurrentRefreshRate"
                ],
                text=True
            )

            return output.strip() + " Hz"

        except Exception:

            return "Unknown"

    def summary(self):

        return {
            "resolution": self.get_current_resolution(),
            "refresh_rate": self.get_refresh_rate()
        }