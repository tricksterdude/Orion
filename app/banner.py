from ui.screen import Screen
from config.version import (
    APP_NAME,
    APP_DESCRIPTION,
    VERSION
)


class Banner(Screen):

    def show(self):

        self.line()

        print(APP_NAME.center(self.WIDTH))
        print(APP_DESCRIPTION.center(self.WIDTH))
        print(f"Version {VERSION}".center(self.WIDTH))

        self.line()
        print()