import psutil


class PlaybackDetector:

    def is_stremio_running(self):

        for process in psutil.process_iter(["name"]):

            try:

                name = process.info["name"]

                if name and "stremio" in name.lower():

                    return True

            except (psutil.NoSuchProcess,
                    psutil.AccessDenied):

                continue

        return False