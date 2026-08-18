from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("CONTAINER UPDATE ROUTE TEST")
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

original_updater_update = (
    routes.container_updater.update
)

try:

    routes.history_store.read = (
        lambda limit=100: []
    )

    routes.service_status.get_all = (
        lambda: []
    )

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.post(
        "/containers/aiostreams/update"
    )

    assert response.status_code == 403

    print("✓ Missing security token rejected")

    response = client.post(
        "/containers/not-allowed/update",
        data={
            "token": (
                routes.container_update_token
            )
        },
    )

    assert response.status_code == 404

    print("✓ Unknown container rejected")

    update_calls = []

    routes.container_update_status.get_all = (
        lambda: [
            {
                "name": "AIOStreams",
                "slug": "aiostreams",
                "status": "current",
                "update_available": False,
                "image": (
                    "ghcr.io/viren070/"
                    "aiostreams:latest"
                ),
            }
        ]
    )

    routes.container_updater.update = (
        lambda slug: update_calls.append(slug)
    )

    response = client.post(
        "/containers/aiostreams/update",
        data={
            "token": (
                routes.container_update_token
            )
        },
    )

    assert response.status_code == 302
    assert update_calls == []
    assert (
        "update_status=current"
        in response.headers["Location"]
    )

    print("✓ Current container not recreated")

    routes.container_update_status.get_all = (
        lambda: [
            {
                "name": "AIOStreams",
                "slug": "aiostreams",
                "status": "available",
                "update_available": True,
                "image": (
                    "ghcr.io/viren070/"
                    "aiostreams:latest"
                ),
            }
        ]
    )

    def successful_update(slug):

        update_calls.append(slug)

        return {
            "ok": True,
            "status": "updated",
            "name": "AIOStreams",
            "slug": slug,
            "message": (
                "AIOStreams updated "
                "successfully."
            ),
        }

    routes.container_updater.update = (
        successful_update
    )

    response = client.post(
        "/containers/aiostreams/update",
        data={
            "token": (
                routes.container_update_token
            )
        },
    )

    assert response.status_code == 302
    assert update_calls == ["aiostreams"]
    assert (
        "update_status=updated"
        in response.headers["Location"]
    )

    print("✓ Available update sent to updater")

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

    routes.container_updater.update = (
        original_updater_update
    )

print()
print("✓ Container update route test passed")