from flask import Flask

from app.api.routes import playback


class OrionAPIServer:

    def __init__(self):

        self.app = Flask("Orion")

        self.app.register_blueprint(playback)

    def start(self):

        self.app.run(

            host="127.0.0.1",

            port=8765,

            debug=False,

            use_reloader=False,

        )