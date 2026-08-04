import platform
import psutil
import subprocess


class HardwareManager:

    def get_computer_name(self):

        return platform.node()

    def get_cpu(self):

        return platform.processor()

    def get_memory_gb(self):

        return round(
            psutil.virtual_memory().total / (1024 ** 3)
        )

    def get_gpu(self):

        try:

            output = subprocess.check_output(
                [
                    "powershell",
                    "-Command",
                    "(Get-CimInstance Win32_VideoController).Name"
                ],
                text=True
            )

            return output.strip()

        except Exception:

            return "Unknown"

    def summary(self):

        return {
            "computer": self.get_computer_name(),
            "cpu": self.get_cpu(),
            "memory": self.get_memory_gb(),
            "gpu": self.get_gpu()
        }