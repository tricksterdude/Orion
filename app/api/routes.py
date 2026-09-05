import hmac
import secrets
import time
from urllib.parse import urlsplit

from flask import (
    Blueprint,
    Response,
    abort,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from app.api.container_updates import (
    ContainerUpdateStatus,
)
from app.api.aiostreams_templates import (
    AIOStreamsTemplateUpdates,
    TemplateUpdateError,
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
from app.api.service_controller import ServiceController
from app.api.service_names import service_slug
from app.api.service_registry import ServiceRegistry
from app.api.service_status import ServiceStatus
from app.audio.guidance_status import audio_guidance_status
from app.audio.spatial_control import SpatialAudioController
from app.audio.windows_output import WindowsAudioOutput
from app.audio.windows_settings import WindowsSoundSettings
from app.cinema_checkup import CinemaCheckup, CinemaCheckupError
from app.display.adapter import DisplayAdapter
from app.display.restore import DisplayRestore
from app.media.title import friendly_media_title
from app.onboarding import OnboardingAssistant, OnboardingError
from app.playback.history import PlaybackHistory
from app.recovery_status import display_recovery_status
from app.receivers.manager import ReceiverManager
from app.secure_settings import (
    SecureSettingsError,
    SecureSettingsStore,
)
from app.setup_profile import (
    SetupProfileError,
    SetupProfileManager,
)
from app.stremio_controller import StremioController
from app.system_diagnostics import SystemDiagnostics


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
service_controller = ServiceController()
stremio_controller = StremioController()
aiostreams_template_updates = (
    AIOStreamsTemplateUpdates()
)
system_diagnostics = SystemDiagnostics(
    service_status=service_status,
    stremio_controller=stremio_controller,
)
secure_settings_store = SecureSettingsStore()
setup_profile_manager = SetupProfileManager()
windows_sound_settings = WindowsSoundSettings()
spatial_audio_controller = SpatialAudioController()
onboarding_assistant = OnboardingAssistant(
    display=DisplayAdapter(),
    audio_output=WindowsAudioOutput(),
    stremio=stremio_controller,
    service_discovery=service_discovery,
)
cinema_checkup = CinemaCheckup(
    diagnostics=system_diagnostics,
    setup_profile=setup_profile_manager,
    display=DisplayAdapter(),
    display_recovery=DisplayRestore(),
    spatial_audio=spatial_audio_controller,
    history=history_store,
)

container_update_token = (
    secrets.token_urlsafe(32)
)

optional_service_token = (
    secrets.token_urlsafe(32)
)

service_registration_token = (
    secrets.token_urlsafe(32)
)

history_management_token = (
    secrets.token_urlsafe(32)
)

history_token_cookie = "orion_history_token"

service_control_token = (
    secrets.token_urlsafe(32)
)

template_update_token = (
    secrets.token_urlsafe(32)
)

settings_management_token = (
    secrets.token_urlsafe(32)
)

audio_guidance_token = (
    secrets.token_urlsafe(32)
)

cinema_checkup_token = (
    secrets.token_urlsafe(32)
)


def _tmdb_setting_status():

    try:
        return {
            "configured": secure_settings_store.configured(
                SecureSettingsStore.TMDB_API_KEY
            ),
            "available": True,
            "message": None,
        }
    except SecureSettingsError as error:
        return {
            "configured": False,
            "available": False,
            "message": str(error),
        }


def _setup_profile_status():

    try:
        profile = setup_profile_manager.snapshot()
        return {
            "available": True,
            "completed": setup_profile_manager.completed(),
            "service_count": len(profile["services"]),
            "provider_count": len(profile["providers"]),
            "message": None,
        }
    except SetupProfileError as error:
        return {
            "available": False,
            "completed": False,
            "service_count": 0,
            "provider_count": 0,
            "message": str(error),
        }


def configure_playback_handler(handler):

    controller.set_handler(handler)


@home.get("/")
def home_route():

    sessions = history_store.read(
        limit=15
    )

    services = service_status.get_all()

    diagnostics_snapshot = system_diagnostics.run(
        services=services
    )

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
        configured_services=services
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
        recovery_status=(
            display_recovery_status.get()
        ),
        diagnostics=diagnostics_snapshot,
        tmdb_setting=_tmdb_setting_status(),
        setup_profile=_setup_profile_status(),
        audio_guidance=audio_guidance_status.get(),
        audio_guidance_token=audio_guidance_token,
    )


@home.get("/audio-guidance/status")
def audio_guidance_status_route():

    response = make_response(
        audio_guidance_status.get()
    )
    response.headers["Cache-Control"] = "no-store"

    return response


@home.post("/audio-guidance/open-settings")
def audio_guidance_settings_route():

    submitted_token = request.form.get(
        "token",
        "",
    )

    if not hmac.compare_digest(
        submitted_token,
        audio_guidance_token,
    ):

        abort(403)

    result = windows_sound_settings.open()

    return redirect(
        url_for(
            "home.home_route",
            update_status=(
                "updated"
                if result["ok"]
                else "failed"
            ),
            update_message=result["message"],
        )
    )


@home.get("/settings")
def settings_route():

    result = None
    result_status = request.args.get(
        "settings_status"
    )
    result_message = request.args.get(
        "settings_message"
    )

    if result_status and result_message:
        result = {
            "status": result_status,
            "message": result_message,
        }

    response = make_response(
        render_template(
            "settings.html",
            tmdb_setting=_tmdb_setting_status(),
            setup_profile=_setup_profile_status(),
            settings_management_token=(
                settings_management_token
            ),
            result=result,
        )
    )
    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )
    response.headers["Pragma"] = "no-cache"

    return response


@home.get("/setup")
def setup_route():

    result = None
    result_status = request.args.get("setup_status")
    result_message = request.args.get("setup_message")

    if result_status and result_message:
        result = {
            "status": result_status,
            "message": result_message,
        }

    try:
        current_profile = setup_profile_manager.snapshot()
        onboarding = onboarding_assistant.snapshot(
            current_profile,
            completed=setup_profile_manager.completed(),
            playback_active=bool(
                audio_guidance_status.get().get("active")
            ),
        )
        profile = onboarding["profile"]
        profile_error = None
    except (SetupProfileError, OnboardingError) as error:
        profile = None
        onboarding = None
        profile_error = str(error)

    detected_display = (
        onboarding["display"]
        if onboarding
        and onboarding["display"]["available"]
        else None
    )

    response = make_response(
        render_template(
            "setup.html",
            profile=profile,
            profile_error=profile_error,
            onboarding=onboarding,
            detected_display=detected_display,
            supported_providers=(
                setup_profile_manager.SUPPORTED_PROVIDERS
            ),
            receiver_adapters=ReceiverManager.options(),
            spatial_audio_setup=spatial_audio_controller.status(),
            settings_management_token=(
                settings_management_token
            ),
            result=result,
        )
    )
    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response


@home.post("/setup/save")
def setup_save_route():

    if not hmac.compare_digest(
        request.form.get("token", ""),
        settings_management_token,
    ):
        abort(403)

    try:
        current = setup_profile_manager.snapshot()
        services = onboarding_assistant.merge_services(
            current["services"],
            request.form.getlist("discovered_services"),
        )
        profile = {
            "version": setup_profile_manager.VERSION,
            "media": {
                "display": {
                    "name": request.form.get(
                        "display_name",
                        "",
                    ),
                    "resolution": request.form.get(
                        "resolution",
                        "",
                    ),
                    "desktop_refresh_rate": request.form.get(
                        "desktop_refresh_rate",
                        "",
                    ),
                    "hdr": (
                        request.form.get("hdr") == "on"
                    ),
                },
                "audio": {
                    "receiver": request.form.get(
                        "receiver",
                        "",
                    ),
                    # Audio format follows the playing content.  The
                    # profile must not imply that Orion forces a codec.
                    "preferred_format": "Automatic",
                    "receiver_adapter": request.form.get(
                        "receiver_adapter",
                        "none",
                    ),
                    "receiver_host": request.form.get(
                        "receiver_host",
                        "",
                    ),
                    "spatial_control": request.form.get(
                        "spatial_control",
                        "guided",
                    ),
                },
                "playback": {
                    "player": request.form.get(
                        "player",
                        "",
                    ),
                    "restore_desktop_after_playback": (
                        request.form.get(
                            "restore_desktop"
                        )
                        == "on"
                    ),
                },
            },
            "services": services,
            "providers": request.form.getlist(
                "providers"
            ),
        }
        setup_profile_manager.save(profile)
        service_status.reload()
        status = "updated"
        message = (
            "The local Orion profile was saved. Restart Orion "
            "before the next playback session."
        )
    except (SetupProfileError, OnboardingError) as error:
        status = "failed"
        message = str(error)

    return redirect(
        url_for(
            "home.setup_route",
            setup_status=status,
            setup_message=message,
        )
    )


@home.post("/settings/profile/export")
def profile_export_route():

    if not hmac.compare_digest(
        request.form.get("token", ""),
        settings_management_token,
    ):
        abort(403)

    try:
        text = setup_profile_manager.export_text()
    except SetupProfileError as error:
        return redirect(
            url_for(
                "home.settings_route",
                settings_status="failed",
                settings_message=str(error),
            )
        )

    response = Response(
        text,
        mimetype="application/json",
    )
    response.headers["Content-Disposition"] = (
        "attachment; filename=orion-profile.json"
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@home.post("/settings/profile/import")
def profile_import_route():

    if not hmac.compare_digest(
        request.form.get("token", ""),
        settings_management_token,
    ):
        abort(403)

    upload = request.files.get("profile")

    try:
        if upload is None or not upload.filename:
            raise SetupProfileError(
                "Choose an Orion profile JSON file."
            )

        content = upload.stream.read(
            setup_profile_manager.MAX_IMPORT_BYTES + 1
        )
        setup_profile_manager.import_bytes(content)
        service_status.reload()
        status = "updated"
        message = (
            "The Orion profile was imported. Restart Orion "
            "before the next playback session."
        )
    except SetupProfileError as error:
        status = "failed"
        message = str(error)

    return redirect(
        url_for(
            "home.settings_route",
            settings_status=status,
            settings_message=message,
        )
    )


@home.post("/settings/tmdb")
def tmdb_settings_route():

    if not hmac.compare_digest(
        request.form.get("token", ""),
        settings_management_token,
    ):
        abort(403)

    action = request.form.get("action", "save")

    try:
        if action == "remove":
            removed = secure_settings_store.delete(
                SecureSettingsStore.TMDB_API_KEY
            )
            status = "updated"
            message = (
                "The TMDb API key was removed."
                if removed
                else "No TMDb API key was stored."
            )
        elif action == "save":
            secure_settings_store.set(
                SecureSettingsStore.TMDB_API_KEY,
                request.form.get("api_key", ""),
            )
            status = "updated"
            message = (
                "The TMDb API key was encrypted and saved "
                "for this Windows account."
            )
        else:
            abort(400)
    except SecureSettingsError as error:
        status = "failed"
        message = str(error)

    return redirect(
        url_for(
            "home.settings_route",
            settings_status=status,
            settings_message=message,
        )
    )


@home.get("/diagnostics")
def diagnostics_route():

    services = service_status.get_all()

    snapshot = system_diagnostics.run(
        services=services,
        force=(
            request.args.get("refresh") == "1"
        ),
    )

    return render_template(
        "diagnostics.html",
        diagnostics=snapshot,
        safe_report=system_diagnostics.report(
            snapshot
        ),
    )


@home.get("/diagnostics/report")
def diagnostics_report_route():

    snapshot = system_diagnostics.run(
        services=service_status.get_all()
    )

    response = Response(
        system_diagnostics.report(snapshot),
        mimetype="text/plain",
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=orion-diagnostics.txt"
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@home.get("/checkup")
def cinema_checkup_route():

    result = None
    result_status = request.args.get(
        "checkup_status"
    )
    result_message = request.args.get(
        "checkup_message"
    )

    if result_status and result_message:
        result = {
            "status": result_status,
            "message": result_message,
        }

    response = make_response(
        render_template(
            "cinema_checkup.html",
            checkup=cinema_checkup.latest(),
            cinema_checkup_token=(
                cinema_checkup_token
            ),
            result=result,
            playback_active=bool(
                audio_guidance_status.get().get("active")
            ),
        )
    )
    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response


@home.post("/checkup/run")
def cinema_checkup_run_route():

    if not hmac.compare_digest(
        request.form.get("token", ""),
        cinema_checkup_token,
    ):
        abort(403)

    try:
        snapshot = cinema_checkup.run(
            services=service_status.get_all(),
            playback_active=bool(
                audio_guidance_status.get().get("active")
            ),
        )
        status = (
            "updated"
            if snapshot["status"] == "healthy"
            else "current"
        )
        message = (
            "Cinema Checkup completed: "
            + snapshot["label"]
            + "."
        )
    except CinemaCheckupError as error:
        status = "failed"
        message = str(error)

    return redirect(
        url_for(
            "home.cinema_checkup_route",
            checkup_status=status,
            checkup_message=message,
        )
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

    service_result = None

    result_status = request.args.get(
        "service_status"
    )

    result_message = request.args.get(
        "service_message"
    )

    if result_status and result_message:

        service_result = {
            "status": result_status,
            "message": result_message,
        }

    stremio_status = None
    template_status = None

    if service["slug"] == "aiostreams":

        stremio_status = (
            stremio_controller.status()
        )

        template_status = (
            aiostreams_template_updates.status(
                service["url"],
                force=(
                    request.args.get(
                        "template_refresh"
                    )
                    == "1"
                ),
            )
        )

    return render_template(
        "service.html",
        service=service,
        service_control_token=service_control_token,
        service_result=service_result,
        stremio_status=stremio_status,
        template_status=template_status,
        template_update_token=(
            template_update_token
        ),
    )


def _valid_template_token():

    return hmac.compare_digest(
        request.form.get("token", ""),
        template_update_token,
    )


def _aiostreams_service():

    service = service_status.get(
        "aiostreams"
    )

    if service is None:
        abort(404)

    return service


@home.post("/services/aiostreams/template/link")
def aiostreams_template_link_route():

    if not _valid_template_token():
        abort(403)

    service = _aiostreams_service()

    try:
        state = aiostreams_template_updates.link(
            service["url"],
            request.form.get("uuid", ""),
            request.form.get("password", ""),
        )

        installed = state.get(
            "applied_version"
        )

        message = (
            "AIOStreams linked securely. "
            + (
                f"Tamtaro {installed} is installed."
                if installed
                else (
                    "No applied Tamtaro Complete version "
                    "was recorded."
                )
            )
        )
        status = "updated"
    except TemplateUpdateError as error:
        status = "failed"
        message = str(error)

    return redirect(
        url_for(
            "home.service_view_route",
            service_slug="aiostreams",
            service_status=status,
            service_message=message,
            template_refresh="1",
        )
    )


@home.post("/services/aiostreams/template/unlink")
def aiostreams_template_unlink_route():

    if not _valid_template_token():
        abort(403)

    service = _aiostreams_service()
    aiostreams_template_updates.unlink(
        service["url"]
    )

    return redirect(
        url_for(
            "home.service_view_route",
            service_slug="aiostreams",
            service_status="updated",
            service_message=(
                "The saved AIOStreams link was removed."
            ),
        )
    )


@home.post("/services/aiostreams/template/update")
def aiostreams_template_update_route():

    if not _valid_template_token():
        abort(403)

    service = _aiostreams_service()

    try:
        launch = (
            aiostreams_template_updates
            .update_launch(
                service["url"],
                urlsplit(
                    request.host_url
                ).hostname,
            )
        )
    except TemplateUpdateError as error:
        return redirect(
            url_for(
                "home.service_view_route",
                service_slug="aiostreams",
                service_status="failed",
                service_message=str(error),
                template_refresh="1",
            )
        )

    response = redirect(launch["target"])

    if launch["auth_mode"] != "session":
        return response

    max_age = max(
        int(
            launch["expires_at"] / 1000
            - time.time()
        ),
        0,
    )

    response.set_cookie(
        "aiostreams.config-session",
        launch["session_token"],
        max_age=max_age,
        httponly=True,
        samesite="Strict",
        path="/api",
    )
    response.set_cookie(
        "aiostreams.has-config-session",
        "1",
        max_age=max_age,
        httponly=False,
        samesite="Strict",
        path="/",
    )

    return response


@home.post("/services/aiostreams/stremio/launch")
def stremio_launch_route():

    submitted_token = request.form.get(
        "token",
        "",
    )

    if not hmac.compare_digest(
        submitted_token,
        service_control_token,
    ):

        abort(403)

    if service_status.get("aiostreams") is None:

        abort(404)

    result = stremio_controller.launch()

    return redirect(
        url_for(
            "home.service_view_route",
            service_slug="aiostreams",
            service_status=(
                "updated"
                if result["ok"]
                else "failed"
            ),
            service_message=result["message"],
        )
    )


@home.post("/services/<requested_slug>/control/<action>")
def service_control_route(requested_slug, action):

    submitted_token = request.form.get(
        "token",
        "",
    )

    if not hmac.compare_digest(
        submitted_token,
        service_control_token,
    ):

        abort(403)

    if action not in service_controller.ALLOWED_ACTIONS:

        abort(404)

    configured_service = next(
        (
            service
            for service in service_status.services
            if service_slug(
                getattr(service, "name", "")
            )
            == service_slug(requested_slug)
        ),
        None,
    )

    if configured_service is None:

        abort(404)

    result = service_controller.control(
        action,
        getattr(
            configured_service,
            "container",
            None,
        ),
    )

    return redirect(
        url_for(
            "home.service_view_route",
            service_slug=requested_slug,
            service_status=(
                "updated"
                if result["ok"]
                else "failed"
            ),
            service_message=result["message"],
        )
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
        "15",
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
        min(limit, 15),
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
        limit=15
    )

    history_result = None

    result_status = request.args.get(
        "history_status"
    )

    result_message = request.args.get(
        "history_message"
    )

    if result_status and result_message:

        history_result = {
            "status": result_status,
            "message": result_message,
        }

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

    browser_token = request.cookies.get(
        history_token_cookie
    )

    if not browser_token or len(browser_token) > 200:
        browser_token = history_management_token

    response = make_response(
        render_template(
            "playback_history.html",
            sessions=sessions,
            history_management_token=browser_token,
            history_result=history_result,
        )
    )
    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )
    response.set_cookie(
        history_token_cookie,
        browser_token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="Strict",
        path="/history",
    )

    return response


def _valid_history_token():

    submitted_token = request.form.get(
        "token",
        "",
    )
    browser_token = request.cookies.get(
        history_token_cookie,
        "",
    )

    return bool(
        submitted_token
        and browser_token
        and len(submitted_token) <= 200
        and len(browser_token) <= 200
        and hmac.compare_digest(
            submitted_token,
            browser_token,
        )
    )


@history.post("/history/<session_id>/delete")
def history_delete_route(session_id):

    if not _valid_history_token():

        abort(403)

    deleted = history_store.delete(session_id)

    if deleted is True:

        result_status = "updated"
        message = "The playback history entry was deleted."

    elif deleted is False:

        result_status = "current"
        message = "That playback history entry no longer exists."

    else:

        result_status = "failed"
        message = "Orion could not delete that history entry."

    return redirect(
        url_for(
            "history.history_view_route",
            history_status=result_status,
            history_message=message,
        )
    )


@history.post("/history/delete-all")
def history_delete_all_route():

    if not _valid_history_token():

        abort(403)

    deleted_count = history_store.clear()

    if deleted_count is None:

        result_status = "failed"
        message = "Orion could not clear playback history."

    elif deleted_count == 0:

        result_status = "current"
        message = "Playback history is already empty."

    else:

        result_status = "updated"
        message = (
            f"Deleted {deleted_count} playback "
            "history entries."
        )

    return redirect(
        url_for(
            "history.history_view_route",
            history_status=result_status,
            history_message=message,
        )
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

    candidate = service_discovery.get_candidate(
        candidate_id,
        configured_services=service_status.services,
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
