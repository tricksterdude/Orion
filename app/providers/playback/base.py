from abc import ABC, abstractmethod


class PlaybackProvider(ABC):

    name = "Unknown"

    def __init__(self, session):

        self.session = session

    @abstractmethod
    def is_available(self):

        pass

    @abstractmethod
    def start(self):

        pass

    @abstractmethod
    def stop(self):

        pass

    def current(self):

        return None