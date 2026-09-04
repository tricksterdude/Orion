import os
from pathlib import Path

try:

    import winreg

except ImportError:

    winreg = None


class SpatialAudioProcessors:

    PROCESSORS = (
        {
            "id": "dolby_access",
            "name": "Dolby Access",
            "markers": (
                "dolbylaboratories.dolbyaccess",
                "dolby access",
            ),
        },
        {
            "id": "dts_sound_unbound",
            "name": "DTS Sound Unbound",
            "markers": (
                "dtsinc.dtssoundunbound",
                "dts sound unbound",
            ),
        },
    )

    PACKAGE_REGISTRY = (
        r"Software\Classes\Local Settings\Software\Microsoft"
        r"\Windows\CurrentVersion\AppModel\Repository\Packages"
    )

    def __init__(self, package_names=None):

        self._configured_names = package_names

    @staticmethod
    def _registry_package_names():

        if winreg is None:

            return []

        names = []

        try:

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                SpatialAudioProcessors.PACKAGE_REGISTRY,
            ) as key:

                index = 0

                while True:

                    try:

                        names.append(winreg.EnumKey(key, index))
                        index += 1

                    except OSError:

                        break

        except OSError:

            pass

        return names

    @staticmethod
    def _directory_package_names():

        local_app_data = os.environ.get("LOCALAPPDATA")

        if not local_app_data:

            return []

        packages = Path(local_app_data) / "Packages"

        try:

            return [
                path.name
                for path in packages.iterdir()
                if path.is_dir()
            ]

        except OSError:

            return []

    def package_names(self):

        if self._configured_names is not None:

            return [
                str(name)
                for name in self._configured_names
            ]

        return list(
            dict.fromkeys(
                self._registry_package_names()
                + self._directory_package_names()
            )
        )

    def installed(self):

        package_text = "\n".join(
            self.package_names()
        ).casefold()

        return [
            {
                "id": processor["id"],
                "name": processor["name"],
            }
            for processor in self.PROCESSORS
            if any(
                marker in package_text
                for marker in processor["markers"]
            )
        ]

    def recommendation(self, immersive_audio):

        format_name = str(
            immersive_audio or ""
        ).strip()

        if format_name == "Dolby Atmos":

            processor_id = "dolby_access"

        elif format_name == "DTS:X":

            processor_id = "dts_sound_unbound"

        else:

            return {
                "policy": "Automatic",
                "processor": None,
                "installed": None,
                "control": "observe_only",
            }

        installed = {
            processor["id"]: processor["name"]
            for processor in self.installed()
        }
        name = next(
            processor["name"]
            for processor in self.PROCESSORS
            if processor["id"] == processor_id
        )

        return {
            "policy": "Automatic",
            "processor": name,
            "installed": processor_id in installed,
            "control": "observe_only",
        }
