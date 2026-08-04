import json
from pathlib import Path


class MediaProfile:

    def __init__(self):

        profile = Path("data/media_profile.json")

        with profile.open(
            "r",
            encoding="utf-8"
        ) as f:

            self.data = json.load(f)

    @property
    def display(self):

        return self.data["display"]

    @property
    def audio(self):

        return self.data["audio"]

    @property
    def playback(self):

        return self.data["playback"]

    def summary(self):

        return {
            "display": self.display["name"],
            "desktop_refresh": self.display["desktop_refresh_rate"],
            "movie_refresh": self.display["movie_refresh_rate"],
            "hdr": self.display["hdr"],
            "receiver": self.audio["receiver"],
            "audio": self.audio["preferred_format"],
            "player": self.playback["player"],
        }