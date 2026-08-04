from app.display.adapter import DisplayAdapter
from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher


class DisplayRestore:

    def __init__(self):

        self.adapter = DisplayAdapter()
        self.switcher = DisplaySwitcher()

        self.original: DisplayMode | None = None

    def save(self):

        self.original = self.adapter.current_mode()

    def has_saved_mode(self) -> bool:

        return self.original is not None

    def original_mode(self):

        return self.original

    def restore(self) -> bool:

        if self.original is None:
            return False

        return self.switcher.switch(self.original)