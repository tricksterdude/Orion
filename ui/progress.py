class ProgressBar:

    def render(self, percent, width=30):

        filled = int(width * percent / 100)

        empty = width - filled

        return "█" * filled + "░" * empty