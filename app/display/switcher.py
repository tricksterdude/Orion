from app.display.adapter import DisplayAdapter


class DisplaySwitcher:

    def __init__(self):

        self.adapter = DisplayAdapter()

    def can_switch(self, width, height, refresh):

        for mode in self.adapter.available_modes():

            if (
                mode["width"] == width
                and mode["height"] == height
                and mode["refresh"] == refresh
            ):
                return True

        return False