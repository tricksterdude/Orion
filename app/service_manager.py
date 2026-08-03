from models.service import Service


class ServiceManager:

    def __init__(self):
        self.services = []

    def register_defaults(self):

        self.services.append(
            Service(
                "NZBDAV",
                "nzbdav",
                8080,
                "http://localhost:8080"
            )
        )

        self.services.append(
            Service(
                "UsenetStreamer",
                "usenetstreamer",
                7001,
                "http://localhost:7001"
            )
        )

        self.services.append(
            Service(
                "NZBHydra2",
                "nzbhydra2",
                5076,
                "http://localhost:5076"
            )
        )

        self.services.append(
            Service(
                "AIOMetadata",
                "aiometadata",
                3232,
                "http://localhost:3232"
            )
        )

        self.services.append(
            Service(
                "AIOStreams",
                "aiostreams",
                3000,
                "http://localhost:3000"
            )
        )

    def get_all(self):
        return self.services