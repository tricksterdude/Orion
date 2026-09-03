from app.media_profile import MediaProfile


class MediaManager:

    def __init__(self):

        self.profile = MediaProfile()

    def get_desktop_refresh_rate(self):

        return self.profile.display["desktop_refresh_rate"]

    def get_display_name(self):

        return self.profile.display["name"]

    def get_resolution(self):

        return self.profile.display["resolution"]

    def hdr_enabled(self):

        return self.profile.display["hdr"]

    def get_receiver(self):

        return self.profile.audio["receiver"]

    def get_audio_format(self):

        return self.profile.audio["preferred_format"]

    def get_player(self):

        return self.profile.playback["player"]

    def restore_desktop_enabled(self):

        return self.profile.playback[
            "restore_desktop_after_playback"
        ]
