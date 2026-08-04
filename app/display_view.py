from ui.screen import Screen


class DisplayView(Screen):

    def show(self, display):

        self.title("DISPLAY")

        print(f"Resolution   : {display['resolution']}")
        print(f"Refresh Rate : {display['refresh_rate']}")

        print()

        self.wait()