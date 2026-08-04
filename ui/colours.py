class Colours:

    RESET = "\033[0m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"

    BOLD = "\033[1m"

    @staticmethod
    def green(text):
        return f"{Colours.GREEN}{text}{Colours.RESET}"

    @staticmethod
    def red(text):
        return f"{Colours.RED}{text}{Colours.RESET}"

    @staticmethod
    def yellow(text):
        return f"{Colours.YELLOW}{text}{Colours.RESET}"

    @staticmethod
    def blue(text):
        return f"{Colours.BLUE}{text}{Colours.RESET}"

    @staticmethod
    def cyan(text):
        return f"{Colours.CYAN}{text}{Colours.RESET}"

    @staticmethod
    def bold(text):
        return f"{Colours.BOLD}{text}{Colours.RESET}"