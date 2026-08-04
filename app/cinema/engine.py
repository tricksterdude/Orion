from app.display.adapter import DisplayAdapter
from app.display.controller import DisplayController
from app.display.mode import DisplayMode
from app.display.switcher import DisplaySwitcher


class CinemaEngine:

    def __init__(self):

        self.adapter = DisplayAdapter()
        self.controller = DisplayController()
        self.switcher = DisplaySwitcher()

    def analyse(self, fps):

        current = self.adapter.current_mode()

        target = DisplayMode(
            width=current.width,
            height=current.height,
            bits=current.bits,
            refresh=self.controller.choose_refresh(fps),
        )

        supported = self.switcher.can_switch(target)

        return {
            "fps": fps,
            "current": current,
            "target": target,
            "supported": supported,
            "simulation": True,
        }