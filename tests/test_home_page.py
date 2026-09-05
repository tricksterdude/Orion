from app.api import routes
from app.api.server import OrionAPIServer
from app.recovery_status import display_recovery_status


print("=" * 60)
print("ORION HOME PAGE TEST")
print("=" * 60)
print()

original_history_read = (
    routes.history_store.read
)

original_service_get_all = (
    routes.service_status.get_all
)

original_update_get_all = (
    routes.container_update_status.get_all
)

original_discover = (
    routes.service_discovery.discover
)

original_system_diagnostics = (
    routes.system_diagnostics
)

original_recovery_status = (
    display_recovery_status.get()
)

try:

    class HomeDiagnostics:

        def run(self, services=None, force=False):

            return {
                "status": "healthy",
                "label": "Healthy",
                "generated_at": (
                    "2026-09-02T12:00:00+00:00"
                ),
                "counts": {
                    "healthy": 7,
                    "warning": 0,
                    "action_required": 0,
                },
                "checks": [
                    {"id": str(index)}
                    for index in range(7)
                ],
            }

    routes.system_diagnostics = HomeDiagnostics()

    routes.history_store.read = (
        lambda limit=100: [
            {"session_id": "one"},
            {"session_id": "two"},
        ]
    )

    routes.service_status.get_all = (
        lambda: [
            {
                "name": "AIOStreams",
                "slug": "aiostreams",
                "container": "aiostreams",
                "port": 3500,
                "url": "http://localhost:3500",
                "healthy": True,
                "status_code": 200,
                "response_time": 12.5,
            },
            {
                "name": "NZBDAV",
                "slug": "nzbdav",
                "container": "nzbdav",
                "port": 8500,
                "url": "http://localhost:8500",
                "healthy": False,
                "status_code": None,
                "response_time": None,
            },
            {
                "name": "NZBHydra2",
                "slug": "nzbhydra2",
                "container": "nzbhydra2",
                "port": 5076,
                "url": "http://localhost:5076",
                "healthy": True,
                "status_code": 200,
                "response_time": 18.4,
            },
        ]
    )

    routes.container_update_status.get_all = (
        lambda: [
            {
                "name": "AIOStreams",
                "slug": "aiostreams",
                "container": "aiostreams",
                "image": (
                    "ghcr.io/viren070/"
                    "aiostreams:latest"
                ),
                "status": "available",
                "update_available": True,
                "installed_digest": (
                    "sha256:" + ("a" * 64)
                ),
                "registry_digest": (
                    "sha256:" + ("b" * 64)
                ),
                "message": "Update available.",
            },
            {
                "name": "UsenetStreamer",
                "slug": "usenetstreamer",
                "container": "usenetstreamer",
                "image": (
                    "gavpyro/"
                    "usenetstreamer:latest"
                ),
                "status": "current",
                "update_available": False,
                "installed_digest": (
                    "sha256:" + ("c" * 64)
                ),
                "registry_digest": (
                    "sha256:" + ("c" * 64)
                ),
                "message": "Up to date.",
            },
        ]
    )

    routes.service_discovery.discover = (
        lambda configured_services=None: {
            "candidates": [
                {
                    "id": "example-service-8088",
                    "name": "example-service",
                    "container": "example-service",
                    "image": "example/service:latest",
                    "port": 8088,
                    "url": "http://localhost:8088",
                    "running": True,
                    "status": "running",
                    "health": "healthy",
                }
            ],
            "errors": [],
        }
    )

    display_recovery_status.set(
        {
            "status": "restored",
            "message": (
                "Orion restored 3840x2160 at 120 Hz."
            ),
        }
    )

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<title>Orion</title>" in page
    assert "Orion is running" in page
    assert "Health &amp; Diagnostics" in page
    assert "System assurance" in page
    assert "7/7" in page
    assert "Checks healthy" in page
    assert "Open diagnostics →" in page
    assert 'href="/diagnostics"' in page

    print("✓ Overall system health links to diagnostics")

    assert "Private configuration" in page
    assert "Settings" in page
    assert 'href="/settings"' in page
    assert "TMDb not configured" in page
    assert "Profile needs review" in page

    print("✓ Private settings link displayed")

    print("✓ Orion home page rendered")

    assert "Display recovered" in page
    assert "restored 3840x2160 at 120 Hz" in page

    print("✓ Startup recovery status displayed")

    assert "Playback History" in page
    assert 'href="/history/view"' in page
    assert "Open history →" in page

    print("✓ Playback history link displayed")

    assert "Live audio guidance" in page
    assert 'id="audio-guidance"' in page
    assert 'action="/audio-guidance/open-settings"' in page
    assert routes.audio_guidance_token in page
    assert "/audio-guidance/status" in page

    print("✓ Live audio guidance panel secured and ready")

    assert "2" in page
    assert "Recent sessions" in page

    print("✓ Recent session count displayed")

    assert "AIOStreams" in page
    assert "localhost:3500" in page
    assert "HTTP 200" in page
    assert "12.5 ms" in page
    assert 'href="/services/aiostreams"' in page

    print("✓ Healthy service displayed")

    assert "NZBDAV" in page
    assert "localhost:8500" in page
    assert "No response" in page
    assert "Attention needed" in page
    assert 'href="/services/nzbdav"' in page

    print("✓ Offline service displayed")
    print("✓ Service detail links displayed")

    assert "NZBHydra2" in page
    assert "Remove NZBHydra2" in page
    assert (
        'action="/services/nzbhydra2/remove"'
        in page
    )
    assert routes.optional_service_token in page
    assert "auto-fit" in page

    print("✓ Optional service removal displayed")
    print("✓ Service grid automatically resizes")

    assert "Discovered services" in page
    assert "example/service:latest" in page
    assert "localhost:8088" in page
    assert (
        'action="/services/discovered/'
        'example-service-8088/add"'
        in page
    )
    assert routes.service_registration_token in page
    assert "Add service" in page

    print("✓ Existing Docker service discovery displayed")

    assert "Container updates" in page
    assert "1 update available" in page
    assert "AIOStreams update available" not in page
    assert "Update AIOStreams" in page
    assert (
        'action="/containers/aiostreams/update"'
        in page
    )
    assert 'name="token"' in page
    assert routes.container_update_token in page
    assert "UsenetStreamer is up to date" in page

    print("✓ Controlled update button displayed")

    routes.container_update_status.get_all = (
        lambda: [
            {
                "name": "AIOStreams",
                "slug": "aiostreams",
                "container": "aiostreams",
                "image": (
                    "ghcr.io/viren070/"
                    "aiostreams:latest"
                ),
                "status": "current",
                "update_available": False,
                "installed_digest": (
                    "sha256:" + ("a" * 64)
                ),
                "registry_digest": (
                    "sha256:" + ("a" * 64)
                ),
                "message": "Up to date.",
            },
            {
                "name": "UsenetStreamer",
                "slug": "usenetstreamer",
                "container": "usenetstreamer",
                "image": (
                    "gavpyro/"
                    "usenetstreamer:latest"
                ),
                "status": "current",
                "update_available": False,
                "installed_digest": (
                    "sha256:" + ("c" * 64)
                ),
                "registry_digest": (
                    "sha256:" + ("c" * 64)
                ),
                "message": "Up to date.",
            },
        ]
    )

    current_response = client.get("/")
    current_page = current_response.get_data(
        as_text=True
    )

    assert current_response.status_code == 200
    assert "No updates available" in current_page
    assert "updates-panel-current" in current_page
    assert 'class="update-list"' not in current_page
    assert "Update AIOStreams" not in current_page

    print("✓ Current containers use compact layout")

    result_response = client.get(
        "/?update_status=updated"
        "&update_message="
        "AIOStreams+updated+successfully."
    )

    result_page = result_response.get_data(
        as_text=True
    )

    assert result_response.status_code == 200
    assert (
        "AIOStreams updated successfully."
        in result_page
    )
    assert (
        "window.history.replaceState"
        in result_page
    )

    print("✓ Update result clears from refresh address")

    assert "</article>" not in page
    assert "AIOStreams · UsenetStreamer" in page
    assert "service’s" in page
    assert "current Windows host address." in page
    assert "â" not in page

    print("✓ Service links close correctly")
    print("✓ Page text encoding is correct")

finally:

    routes.history_store.read = (
        original_history_read
    )

    routes.service_status.get_all = (
        original_service_get_all
    )

    routes.container_update_status.get_all = (
        original_update_get_all
    )

    routes.service_discovery.discover = (
        original_discover
    )

    routes.system_diagnostics = (
        original_system_diagnostics
    )

    display_recovery_status.set(
        original_recovery_status
    )

print()
print("✓ Orion home page test passed")
