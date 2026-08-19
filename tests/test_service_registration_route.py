from types import SimpleNamespace

from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("SERVICE REGISTRATION ROUTE TEST")
print("=" * 60)
print()


original_services = routes.service_status.services
original_reload = routes.service_status.reload
original_get_candidate = (
    routes.service_discovery.get_candidate
)
original_add = routes.service_registry.add

try:

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.post(
        "/services/discovered/example-8088/add",
    )

    assert response.status_code == 403

    print("✓ Missing security token rejected")

    routes.service_status.services = [
        SimpleNamespace(
            name="AIOStreams",
            container="aiostreams",
            port=3500,
            url="http://localhost:3500",
        ),
    ]

    candidate_calls = []

    def missing_candidate(
        candidate_id,
        configured_containers=None,
    ):

        candidate_calls.append(
            (
                candidate_id,
                configured_containers,
            )
        )

        return None

    routes.service_discovery.get_candidate = (
        missing_candidate
    )

    response = client.post(
        "/services/discovered/missing-8088/add",
        data={
            "token": routes.service_registration_token,
        },
    )

    assert response.status_code == 302
    assert candidate_calls == [
        (
            "missing-8088",
            {"aiostreams"},
        )
    ]
    assert "no+longer+available" in (
        response.headers["Location"]
    )

    print("✓ Stale discovery candidate rejected")

    candidate = {
        "id": "example-8088",
        "name": "example",
        "container": "example",
        "port": 8088,
        "url": "http://localhost:8088",
    }

    routes.service_discovery.get_candidate = (
        lambda candidate_id, configured_containers=None: (
            candidate
        )
    )

    add_calls = []
    reload_calls = []

    def successful_add(
        selected_candidate,
        display_name=None,
    ):

        add_calls.append(
            (
                selected_candidate,
                display_name,
            )
        )

        return {
            "status": "added",
            "message": (
                "Example Service was added "
                "to Orion successfully."
            ),
        }

    routes.service_registry.add = successful_add
    routes.service_status.reload = (
        lambda: reload_calls.append(True)
    )

    response = client.post(
        "/services/discovered/example-8088/add",
        data={
            "token": routes.service_registration_token,
            "name": "Example Service",
        },
    )

    assert response.status_code == 302
    assert add_calls == [
        (
            candidate,
            "Example Service",
        )
    ]
    assert reload_calls == [True]
    assert "update_status=updated" in (
        response.headers["Location"]
    )

    print("✓ Current candidate registered safely")
    print("✓ Service list refreshed after registration")

finally:

    routes.service_status.services = original_services
    routes.service_status.reload = original_reload
    routes.service_discovery.get_candidate = (
        original_get_candidate
    )
    routes.service_registry.add = original_add


print()
print("✓ Service registration route test passed")
