from app.events.events import MetadataLoadedEvent
from app.technical.manager import TechnicalManager


class CinemaSubscriber:

    def __init__(self, bus, cinema, media):

        self.cinema = cinema
        self.media = media

        self.technical = TechnicalManager()

        bus.subscribe(
            MetadataLoadedEvent,
            self.metadata_loaded,
        )

    def metadata_loaded(self, event):

        #
        # Retrieve the current MovieContext
        #
        context = self.media.current()

        #
        # Analyse the technical information
        #
        technical = self.technical.analyse(context)

        print()

        print("=" * 60)
        print("TECHNICAL METADATA")
        print("=" * 60)
        print()

        print("FPS         :", technical.fps)
        print("Resolution  :", technical.resolution)
        print("HDR         :", technical.hdr)
        print("Video Codec :", technical.video_codec)
        print("Audio Codec :", technical.audio_codec)

        print()

        print("=" * 60)
        print("CINEMA ANALYSIS")
        print("=" * 60)

        print()

        self.cinema.begin(technical.fps)