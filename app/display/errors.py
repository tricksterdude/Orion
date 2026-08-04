class DisplayError(Exception):
    """Base display exception."""


class UnsupportedDisplayMode(DisplayError):
    """Requested display mode is unsupported."""


class DisplaySwitchFailed(DisplayError):
    """Windows failed to switch display mode."""