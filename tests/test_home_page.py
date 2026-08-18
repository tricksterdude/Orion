from app.api import routes
from app.api.server import OrionAPIServer


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

try:

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

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<title>Orion</title>" in page
    assert "Orion is running" in page

    print("✓ Orion home page rendered")

    assert "Playback History" in page
    assert 'href="/history/view"' in page
    assert "Open history →" in page

    print("✓ Playback history link displayed")

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

    assert "Container updates" in page
    assert "1 update available" in page
    assert "AIOStreams update available" in page
    assert "UsenetStreamer is up to date" in page

    print("✓ Container update status displayed")

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

print()
print("✓ Orion home page test passed")