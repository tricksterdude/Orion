from ui.screen import Screen
from config.version import (
    APP_NAME,
    APP_DESCRIPTION,
    VERSION,
    AUTHOR
)


class About(Screen):

    def show(self):

        self.title("ABOUT")

        print(f"Application : {APP_NAME}")
        print(f"Description : {APP_DESCRIPTION}")
        print(f"Version     : {VERSION}")
        print(f"Author      : {AUTHOR}")
        print("GitHub      : tricksterdude/Orion")
        print("Python      : 3.14")
        print("Docker      : Connected")

        print()

        self.wait()