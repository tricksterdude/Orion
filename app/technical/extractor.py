from app.technical.models import TechnicalMetadata


class TechnicalExtractor:

    def extract(self, context):

        #
        # Placeholder.
        #
        # Later this class will inspect the actual
        # movie stream using ffprobe, MediaInfo,
        # or another backend.
        #

        return TechnicalMetadata(

            fps=23.976,

            resolution="3840x2160",

            hdr=False,

            dolby_vision=False,

            video_codec="Unknown",

            audio_codec="Unknown",

            audio_channels="Unknown",

            bitrate=None,
        )