from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("ORION HOME PAGE TEST")
print("=" * 60)
print()

original_read = routes.history_store.read

try:

    routes.history_store.read = (
        lambda limit=100: [
            {"session_id": "one"},
            {"session_id": "two"},
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

    print("✓ Playback history link displayed")

    assert "2" in page
    assert "Recent sessions" in page

    print("✓ Recent session count displayed")

finally:

    routes.history_store.read = original_read

print()
print("✓ Orion home page test passed")