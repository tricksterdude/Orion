from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("SERVICE DETAILS PAGE TEST")
print("=" * 60)
print()


class TestServiceStatus:

    def get(self, requested_slug):

        if requested_slug != "nzbdav":

            return None

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

try:

    routes.service_status = (
        TestServiceStatus()
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

finally:

    routes.service_status = (
        original_service_status
    )

print()
print(
    "✓ Service details page test passed"
)