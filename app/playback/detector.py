import psutil


class PlaybackDetector:

    def __init__(self):

        self.previous = False

    def is_stremio_running(self):

        for process in psutil.process_iter(["name"]):

            try:

                name = process.info["name"]

                if name and "stremio" in name.lower():
                    return True

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                continue

        return False

    def update(self):

        current = self.is_stremio_running()

        started = current and not self.previous
        stopped = self.previous and not current

        self.previous = current

        return {
            "running": current,
            "started": started,
            "stopped": stopped,
        }