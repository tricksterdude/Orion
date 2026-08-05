from flask import Blueprint, request

from app.api.controllers.playback import PlaybackController
from app.api.models import PlaybackRequest


playback = Blueprint("playback", __name__)

controller = PlaybackController()


@playback.post("/playback")
def playback_route():

    data = request.get_json(force=True)

    controller.play(

        PlaybackRequest(**data)

    )

    return {"status": "ok"}