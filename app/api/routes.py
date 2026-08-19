import hmac
import secrets

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

from app.api.container_updates import (
    ContainerUpdateStatus,
)
from app.api.container_updater import (
    ContainerUpdater,
)
from app.api.controllers.playback import PlaybackController
from app.api.models import PlaybackRequest
from app.api.optional_services import (
    OptionalServiceManager,
)
from app.api.service_discovery import (
    ContainerServiceDiscovery,
)
from app.api.service_registry import ServiceRegistry
from app.api.service_status import ServiceStatus
from app.media.title import friendly_media_title
from app.playback.history import PlaybackHistory


home = Blueprint("home", __name__)
playback = Blueprint("playback", __name__)
history = Blueprint("history", __name__)

controller = PlaybackController()
history_store = PlaybackHistory()
service_status = ServiceStatus()
container_update_status = ContainerUpdateStatus()

container_updater = ContainerUpdater(
    status_checker=container_update_status,
)

optional_service_manager = (
    OptionalServiceManager()
)

service_discovery = ContainerServiceDiscovery()
service_registry = ServiceRegistry()

container_update_token = (
    secrets.token_urlsafe(32)
)

optional_service_token = (
    secrets.token_urlsafe(32)
)

service_registration_token = (
    secrets.token_urlsafe(32)
)


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

    container_updates = (
        container_update_status.get_all()
    )

    update_count = sum(
        1
        for container in container_updates
        if container["update_available"] is True
    )

    configured_containers = {
        service.get("container")
        for service in services
        if service.get("container")
    }

    discovery_result = service_discovery.discover(
        configured_containers=configured_containers
    )

    optional_services = [
        {
            "name": definition["name"],
            "slug": definition["slug"],
            "container": definition["container"],
        }
        for definition
        in optional_service_manager.optional_services.values()
        if (
            definition["container"]
            in configured_containers
        )
    ]

    update_result = None

    update_status = request.args.get(
        "update_status"
    )

    update_message = request.args.get(
        "update_message"
    )

    if update_status and update_message:

        update_result = {
            "status": update_status,
            "message": update_message,
        }

    return render_template(
        "home.html",
        session_count=len(sessions),
        services=services,
        healthy_count=healthy_count,
        container_updates=container_updates,
        update_count=update_count,
        container_update_token=(
            container_update_token
        ),
        optional_services=optional_services,
        optional_service_token=(
            optional_service_token
        ),
        discovered_services=(
            discovery_result["candidates"]
        ),
        discovery_errors=(
            discovery_result["errors"]
        ),
        service_registration_token=(
            service_registration_token
        ),
        update_result=update_result,
    )


@home.post("/containers/<container_slug>/update")
def container_update_route(container_slug):

    submitted_token = request.form.get(
        "token",
        "",
    )

    if not hmac.compare_digest(
        submitted_token,
        container_update_token,
    ):

        abort(403)

    if (
        container_slug
        not in container_updater.containers
    ):

        abort(404)

    update_information = next(
        (
            container
            for container
            in container_update_status.get_all()
            if (
                container["slug"]
                == container_slug
            )
        ),
        None,
    )

    if (
        update_information is None
        or (
            update_information[
                "update_available"
            ]
            is not True
        )
    ):

        return redirect(
            url_for(
                "home.home_route",
                update_status="current",
                update_message=(
                    "No update is currently "
                    "available for that container."
                ),
            )
        )

    result = container_updater.update(
        container_slug
    )

    return redirect(
        url_for(
            "home.home_route",
            update_status=result["status"],
            update_message=result["message"],
        )
    )


@home.post("/services/<service_slug>/remove")
def optional_service_remove_route(service_slug):

    submitted_token = request.form.get(
        "token",
        "",
    )

    if not hmac.compare_digest(
        submitted_token,
        optional_service_token,
    ):

        abort(403)

    definition = (
        optional_service_manager
        .optional_services
        .get(service_slug)
    )

    if definition is None:

        abort(404)

    configured = any(
        getattr(
            service,
            "container",
            None,
        )
        == definition["container"]
        for service in service_status.services
    )

    if not configured:

        return redirect(
            url_for(
                "home.home_route",
                update_status="current",
                update_message=(
                    f"{definition['name']} "
                    "has already been removed."
                ),
            )
        )

    result = (
        optional_service_manager.remove(
            service_slug
        )
    )

    if result["ok"]:

        service_status.reload()

    result_status = result["status"]

    if result["ok"]:

        result_status = "updated"

    return redirect(
        url_for(
            "home.home_route",
            update_status=result_status,
            update_message=result["message"],
        )
    )


@home.get("/services/<service_slug>")
def service_view_route(service_slug):

    service = service_status.get(
        service_slug
    )

    if service is None:

        abort(404)

    return render_template(
        "service.html",
        service=service,
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


@home.post("/services/discovered/<candidate_id>/add")
def discovered_service_add_route(candidate_id):

    submitted_token = request.form.get(
        "token",
        "",
    )

    if not hmac.compare_digest(
        submitted_token,
        service_registration_token,
    ):

        abort(403)

    configured_containers = {
        getattr(service, "container", None)
        for service in service_status.services
        if getattr(service, "container", None)
    }

    candidate = service_discovery.get_candidate(
        candidate_id,
        configured_containers=configured_containers,
    )

    if candidate is None:

        return redirect(
            url_for(
                "home.home_route",
                update_status="current",
                update_message=(
                    "That Docker service is no longer "
                    "available to add."
                ),
            )
        )

    result = service_registry.add(
        candidate,
        display_name=request.form.get("name"),
    )

    if result["status"] == "added":

        service_status.reload()

    result_status = result["status"]

    if result_status == "added":

        result_status = "updated"

    elif result_status == "exists":

        result_status = "current"

    return redirect(
        url_for(
            "home.home_route",
            update_status=result_status,
            update_message=result["message"],
        )
    )
