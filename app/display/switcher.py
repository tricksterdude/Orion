import ctypes

from app.display.adapter import DisplayAdapter
from app.display.constants import (
    CDS_TEST,
    DISP_CHANGE_SUCCESSFUL,
    ENUM_CURRENT_SETTINGS,
)
from app.display.devmode import DEVMODE
from app.display.mode import DisplayMode


class DisplaySwitcher:

    def __init__(self):

        self.user32 = ctypes.windll.user32
        self.adapter = DisplayAdapter()

    def can_switch(self, target: DisplayMode) -> bool:

        return target in self.adapter.available_modes()

    def _build_devmode(self, target: DisplayMode):

        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)

        success = self.user32.EnumDisplaySettingsW(
            None,
            ENUM_CURRENT_SETTINGS,
            ctypes.byref(devmode),
        )

        if not success:
            return None

        devmode.dmPelsWidth = target.width
        devmode.dmPelsHeight = target.height
        devmode.dmBitsPerPel = target.bits
        devmode.dmDisplayFrequency = target.refresh

        return devmode

    def test_switch(self, target: DisplayMode) -> bool:

        devmode = self._build_devmode(target)

        if devmode is None:
            return False

        result = self.user32.ChangeDisplaySettingsExW(
            None,
            ctypes.byref(devmode),
            None,
            CDS_TEST,
            None,
        )

        return result == DISP_CHANGE_SUCCESSFUL