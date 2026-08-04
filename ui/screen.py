import os

from ui.colours import Colours


class Screen:

    WIDTH = 60

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def line(self):
        print(Colours.cyan("─" * self.WIDTH))

    def title(self, text):

        self.line()

        print(
            Colours.bold(
                Colours.cyan(
                    text.center(self.WIDTH)
                )
            )
        )

        self.line()

        print()

    def success(self, text):
        print(Colours.green(text))

    def warning(self, text):
        print(Colours.yellow(text))

    def error(self, text):
        print(Colours.red(text))

    def info(self, text):
        print(Colours.blue(text))

    def wait(self):
        input("Press ENTER...")