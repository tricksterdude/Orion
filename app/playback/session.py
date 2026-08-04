class PlaybackSession:

    def __init__(self):

        self.reset()

    def reset(self):

        self.active = False

        self.player = None

        self.title = None

        self.resolution = None

        self.frame_rate = None

        self.hdr = None

        self.audio = None

        self.original_refresh = None

        self.current_refresh = None

    def start(self):

        self.active = True

    def stop(self):

        self.active = False

    def is_active(self):

        return self.active