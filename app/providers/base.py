from abc import ABC, abstractmethod

from app.media.models import MediaState


class MediaProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def current_media(self) -> MediaState:
        ...