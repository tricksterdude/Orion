from app.display.adapter import DisplayAdapter


class DisplaySwitcher:

    def __init__(self):

        self.adapter = DisplayAdapter()

    def can_switch(self, target):

        for mode in self.adapter.available_modes():

            if (
                mode["width"] == target["width"]
                and mode["height"] == target["height"]
                and mode["refresh"] == target["refresh"]
            ):
                return True

        return False