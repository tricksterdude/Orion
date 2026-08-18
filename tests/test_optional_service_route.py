from types import SimpleNamespace

from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("OPTIONAL SERVICE ROUTE TEST")
print("=" * 60)
print()

original_services = (
    routes.service_status.services
)

original_reload = (
    routes.service_status.reload
)

original_remove = (
    routes.optional_service_manager.remove
)

try:

    server = OrionAPIServer()
    client = server.app.test_client()

    missing_token_response = client.post(
        "/services/nzbhydra2/remove",
        data={},
    )

    assert (
        missing_token_response.status_code
        == 403
    )

    print("✓ Missing security token rejected")

    unknown_response = client.post(
        "/services/not-allowed/remove",
        data={
            "token": (
                routes.optional_service_token
            ),
        },
    )

    assert unknown_response.status_code == 404

    print("✓ Unknown service rejected")

    routes.service_status.services = [
        SimpleNamespace(
            name="NZBDAV",
            container="nzbdav",
            port=8500,
            url="http://localhost:8500",
        ),
    ]

    already_removed_response = client.post(
        "/services/nzbhydra2/remove",
        data={
            "token": (
                routes.optional_service_token
            ),
        },
    )

    assert (
        already_removed_response.status_code
        == 302
    )

    already_removed_location = (
        already_removed_response.headers[
            "Location"
        ]
    )

    assert "already+been+removed" in (
        already_removed_location
    )

    print("✓ Already removed service handled safely")

    routes.service_status.services = [
        SimpleNamespace(
            name="NZBHydra2",
            container="nzbhydra2",
            port=5076,
            url="http://localhost:5076",
        ),
    ]

    remove_calls = []
    reload_calls = []

    def fake_remove(slug):

        remove_calls.append(slug)

        return {
            "ok": True,
            "status": "removed",
            "name": "NZBHydra2",
            "slug": "nzbhydra2",
            "message": (
                "NZBHydra2 was removed "
                "successfully."
            ),
        }

    def fake_reload():

        reload_calls.append(True)

        return []

    routes.optional_service_manager.remove = (
        fake_remove
    )

    routes.service_status.reload = (
        fake_reload
    )

    remove_response = client.post(
        "/services/nzbhydra2/remove",
        data={
            "token": (
                routes.optional_service_token
            ),
        },
    )

    assert remove_response.status_code == 302
    assert remove_calls == ["nzbhydra2"]
    assert reload_calls == [True]

    remove_location = (
        remove_response.headers["Location"]
    )

    assert "update_status=updated" in (
        remove_location
    )

    assert (
        "NZBHydra2+was+removed+successfully."
        in remove_location
    )

    print("✓ Allowed optional service sent to manager")
    print("✓ Service list refreshed after removal")

finally:

    routes.service_status.services = (
        original_services
    )

    routes.service_status.reload = (
        original_reload
    )

    routes.optional_service_manager.remove = (
        original_remove
    )

print()
print("✓ Optional service route test passed")