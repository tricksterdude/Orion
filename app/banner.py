from ui.screen import Screen
from config.version import VERSION


class Banner(Screen):

    def show(self):

        self.line()

        print("ORION".center(self.WIDTH))
        print("Home Cinema Operations Console".center(self.WIDTH))
        print(f"v{VERSION}".center(self.WIDTH))

        self.line()
        print()