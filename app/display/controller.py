class DisplayController:

    MOVIE_MAP = {
        23.976: 23,
        24.000: 24,
        25.000: 25,
        29.970: 29,
        30.000: 30,
        50.000: 50,
        59.940: 59,
        60.000: 60,
    }

    def choose_refresh(self, fps):

        closest = min(
            self.MOVIE_MAP.keys(),
            key=lambda value: abs(value - fps)
        )

        return self.MOVIE_MAP[closest]
    