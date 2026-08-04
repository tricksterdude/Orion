from app.display.controller import DisplayController
from app.display.switcher import DisplaySwitcher
from app.display.adapter import DisplayAdapter


class CinemaEngine:

    def __init__(self):

        self.controller = DisplayController()
        self.switcher = DisplaySwitcher()
        self.adapter = DisplayAdapter()

    def analyse(self, fps):

        current = self.adapter.current_mode()

        refresh = self.controller.choose_refresh(fps)

        target = {
            "width": current["width"],
            "height": current["height"],
            "refresh": refresh,
            "bits": current["bits"],
        }

        supported = self.switcher.can_switch(target)

        return {
            "fps": fps,
            "current": current,
            "target": target,
            "supported": supported,
            "simulation": True,
        }