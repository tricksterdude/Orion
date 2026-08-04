from ui.screen import Screen


class HardwareView(Screen):

    def show(self, hardware):

        self.title("HARDWARE")

        print(f"Computer : {hardware['computer']}")
        print(f"CPU      : {hardware['cpu']}")
        print(f"Memory   : {hardware['memory']} GB")
        print(f"GPU      : {hardware['gpu']}")

        print()

        self.wait()