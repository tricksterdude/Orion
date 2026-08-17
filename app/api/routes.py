from flask import (
    Blueprint,
    render_template,
    request,
)

from app.api.controllers.playback import PlaybackController
from app.api.models import PlaybackRequest
from app.playback.history import PlaybackHistory


playback = Blueprint("playback", __name__)
history = Blueprint("history", __name__)

controller = PlaybackController()
history_store = PlaybackHistory()


def configure_playback_handler(handler):

    controller.set_handler(handler)


@playback.post("/playback")
def playback_route():

    data = request.get_json(force=True)

    controller.play(
        PlaybackRequest(**data)
    )

    return {"status": "ok"}


@history.get("/history")
def history_route():

    requested_limit = request.args.get(
        "limit",
        "20",
    )

    try:

        limit = int(requested_limit)

    except ValueError:

        return {
            "error": (
                "limit must be a whole number"
            )
        }, 400

    limit = max(
        1,
        min(limit, 100),
    )

    sessions = history_store.read(
        limit=limit
    )

    return {
        "count": len(sessions),
        "sessions": sessions,
    }


@history.get("/history/view")
def history_view_route():

    sessions = history_store.read(
        limit=50
    )

    return render_template(
        "playback_history.html",
        sessions=sessions,
    )