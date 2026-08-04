from app.media.models import MediaState


class MediaSession:

    def __init__(self):

        self.state = MediaState()

    def update(self, state: MediaState):

        self.state = state

    def current(self):

        return self.state