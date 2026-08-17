class DisplayResult:

    def __init__(
        self,
        success=False,
        message="",
        previous=None,
        current=None,
    ):

        self.success = success
        self.message = message
        self.previous = previous
        self.current = current