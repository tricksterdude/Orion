from flask import (
    Blueprint,
    render_template,
    request,
)

from app.api.controllers.playback import PlaybackController
from app.api.models import PlaybackRequest
from app.api.service_status import ServiceStatus
from app.media.title import friendly_media_title
from app.playback.history import PlaybackHistory


home = Blueprint("home", __name__)
playback = Blueprint("playback", __name__)
history = Blueprint("history", __name__)

controller = PlaybackController()
history_store = PlaybackHistory()
service_status = ServiceStatus()


def configure_playback_handler(handler):

    controller.set_handler(handler)


@home.get("/")
def home_route():

    sessions = history_store.read(
        limit=100
    )

    services = service_status.get_all()

    healthy_count = sum(
        1
        for service in services
        if service["healthy"]
    )

    return render_template(
        "home.html",
        session_count=len(sessions),
        services=services,
        healthy_count=healthy_count,
    )


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

    for session in sessions:

        playback_data = session.get(
            "playback"
        )

        if not isinstance(
            playback_data,
            dict,
        ):

            continue

        if not playback_data.get("title"):

            playback_data["title"] = (
                friendly_media_title(
                    playback_data.get(
                        "filename"
                    )
                )
            )

    return render_template(
        "playback_history.html",
        sessions=sessions,
    )