import ctypes
from ctypes import wintypes

ENUM_CURRENT_SETTINGS = -1


class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPositionX", wintypes.LONG),
        ("dmPositionY", wintypes.LONG),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
    ]


class DisplayAdapter:

    def __init__(self):
        self.user32 = ctypes.windll.user32

    def current_mode(self):

        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)

        success = self.user32.EnumDisplaySettingsW(
            None,
            ENUM_CURRENT_SETTINGS,
            ctypes.byref(devmode)
        )

        if not success:
            return None

        return {
            "width": devmode.dmPelsWidth,
            "height": devmode.dmPelsHeight,
            "refresh": devmode.dmDisplayFrequency,
            "bits": devmode.dmBitsPerPel,
        }

    def available_modes(self):

        modes = []
        index = 0

        while True:

            devmode = DEVMODE()
            devmode.dmSize = ctypes.sizeof(DEVMODE)

            success = self.user32.EnumDisplaySettingsW(
                None,
                index,
                ctypes.byref(devmode)
            )

            if not success:
                break

            mode = {
                "width": devmode.dmPelsWidth,
                "height": devmode.dmPelsHeight,
                "refresh": devmode.dmDisplayFrequency,
                "bits": devmode.dmBitsPerPel,
            }

            if mode not in modes:
                modes.append(mode)

            index += 1

        return modes

    def cinema_modes(self):

        modes = []

        for mode in self.available_modes():

            if mode["width"] != 3840:
                continue

            if mode["height"] != 2160:
                continue

            if mode not in modes:
                modes.append(mode)

        return sorted(modes, key=lambda m: m["refresh"])