from types import SimpleNamespace

from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("SERVICE DETAILS PAGE TEST")
print("=" * 60)
print()


class TestServiceStatus:

    services = [
        SimpleNamespace(
            name="NZBDAV",
            container="nzbdav",
            port=8500,
            url="http://localhost:8500",
        ),
        SimpleNamespace(
            name="AIOStreams",
            container="aiostreams",
            port=3500,
            url="http://localhost:3500",
        ),
    ]

    def get(self, requested_slug):

        if requested_slug not in {
            "nzbdav",
            "aiostreams",
        }:

            return None

        if requested_slug == "aiostreams":

            return {
                "name": "AIOStreams",
                "slug": "aiostreams",
                "container": "aiostreams",
                "port": 3500,
                "url": "http://localhost:3500",
                "healthy": True,
                "status_code": 200,
                "response_time": 15.0,
            }

        return {
            "name": "NZBDAV",
            "slug": "nzbdav",
            "container": "nzbdav",
            "port": 8500,
            "url": "http://localhost:8500",
            "healthy": True,
            "status_code": 200,
            "response_time": 24.5,
        }


original_service_status = (
    routes.service_status
)

original_control = (
    routes.service_controller.control
)

original_stremio_controller = (
    routes.stremio_controller
)

original_template_updates = (
    routes.aiostreams_template_updates
)


class TestStremioController:

    def __init__(self):

        self.launches = 0

    def status(self):

        return {
            "state": "stopped",
            "ready": False,
            "can_launch": True,
            "message": (
                "Launch Stremio with Orion to enable "
                "AIOStreams playback detection."
            ),
        }

    def launch(self):

        self.launches += 1

        return {
            "ok": True,
            "message": "Stremio launched safely.",
        }


class TestTemplateUpdates:

    def status(self, _base_url, force=False):

        return {
            "linked": False,
            "state": "unlinked",
            "name": "Tamtaro Complete SEL Setup",
            "installed_version": None,
            "latest_version": "3.2.2",
            "update_available": False,
            "message": (
                "Link your saved AIOStreams configuration once."
            ),
        }

try:

    routes.service_status = (
        TestServiceStatus()
    )
    routes.stremio_controller = (
        TestStremioController()
    )
    routes.aiostreams_template_updates = (
        TestTemplateUpdates()
    )

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get(
        "/services/nzbdav"
    )

    assert response.status_code == 200

    page = response.get_data(
        as_text=True
    )

    assert "NZBDAV" in page
    assert "Service healthy" in page
    assert "8500" in page
    assert "HTTP status" in page
    assert "200" in page
    assert "24.5 ms" in page
    assert "nzbdav" in page
    assert "Open Web UI" in page
    assert "http://localhost:8500" in page
    assert "Back to Orion" in page
    assert "Restart" in page
    assert "Stop" in page
    assert (
        'action="/services/nzbdav/control/restart"'
        in page
    )
    assert (
        'action="/services/nzbdav/control/stop"'
        in page
    )
    assert routes.service_control_token in page

    aiostreams_response = client.get(
        "/services/aiostreams"
    )

    assert aiostreams_response.status_code == 200

    aiostreams_page = (
        aiostreams_response.get_data(
            as_text=True
        )
    )

    assert "Playback detection" in aiostreams_page
    assert "Template updates" in aiostreams_page
    assert "Link securely" in aiostreams_page
    assert "Launch Stremio" in aiostreams_page
    assert (
        'action="/services/aiostreams/stremio/launch"'
        in aiostreams_page
    )

    missing_launch_token = client.post(
        "/services/aiostreams/stremio/launch"
    )

    assert missing_launch_token.status_code == 403

    launch_response = client.post(
        "/services/aiostreams/stremio/launch",
        data={
            "token": routes.service_control_token,
        },
    )

    assert launch_response.status_code == 302
    assert routes.stremio_controller.launches == 1

    print("✓ AIOStreams launch control secured")

    control_calls = []

    def successful_control(action, container):

        control_calls.append(
            (action, container)
        )

        return {
            "ok": True,
            "status": f"{action}ed",
            "message": "Service action completed.",
        }

    routes.service_controller.control = (
        successful_control
    )

    missing_token_response = client.post(
        "/services/nzbdav/control/stop"
    )

    assert missing_token_response.status_code == 403

    stop_response = client.post(
        "/services/nzbdav/control/stop",
        data={
            "token": routes.service_control_token,
        },
    )

    restart_response = client.post(
        "/services/nzbdav/control/restart",
        data={
            "token": routes.service_control_token,
        },
    )

    assert stop_response.status_code == 302
    assert restart_response.status_code == 302
    assert control_calls == [
        ("stop", "nzbdav"),
        ("restart", "nzbdav"),
    ]

    missing_response = client.get(
        "/services/not-a-service"
    )

    assert missing_response.status_code == 404

    print(
        "✓ Service details page rendered"
    )
    print(
        "✓ Live health details displayed"
    )
    print(
        "✓ Local Web UI link displayed"
    )
    print(
        "✓ Unknown service rejected safely"
    )
    print(
        "✓ Stop and restart controls secured"
    )

finally:

    routes.service_status = (
        original_service_status
    )

    routes.service_controller.control = (
        original_control
    )

    routes.stremio_controller = (
        original_stremio_controller
    )

    routes.aiostreams_template_updates = (
        original_template_updates
    )

print()
print(
    "✓ Service details page test passed"
)
