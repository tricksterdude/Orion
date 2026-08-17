from flask import Flask

from app.api.routes import (
    configure_playback_handler,
    playback,
)


class OrionAPIServer:

    def __init__(self, on_playback=None):

        self.app = Flask("Orion")

        configure_playback_handler(on_playback)

        self.app.register_blueprint(playback)

    def start(self):

        self.app.run(
            host="127.0.0.1",
            port=8765,
            debug=False,
            use_reloader=False,
        )