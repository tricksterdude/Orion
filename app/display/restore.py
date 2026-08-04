class DisplayRestore:

    def __init__(self):

        self.original_mode = None

    def save(self, mode):

        self.original_mode = mode.copy()

    def current(self):

        return self.original_mode

    def clear(self):

        self.original_mode = None