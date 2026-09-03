from types import SimpleNamespace

from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("AIOSTREAMS TEMPLATE ROUTE TEST")
print("=" * 60)
print()


class TestServiceStatus:

    services = [
        SimpleNamespace(
            name="AIOStreams",
            container="aiostreams",
            port=3500,
            url="http://localhost:3500",
        )
    ]

    def get(self, slug):

        if slug != "aiostreams":
            return None

        return {
            "name": "AIOStreams",
            "slug": "aiostreams",
            "container": "aiostreams",
            "port": 3500,
            "url": "http://localhost:3500",
            "healthy": True,
            "status_code": 200,
            "response_time": 10.0,
        }


class TestStremioController:

    def status(self):

        return {
            "state": "ready",
            "ready": True,
            "can_launch": False,
            "message": "Playback detection ready.",
        }


class TestTemplateUpdates:

    def __init__(self):

        self.links = []
        self.unlinks = 0
        self.launches = []
        self.legacy = False

    def status(self, base_url, force=False):

        assert base_url == "http://localhost:3500"

        return {
            "linked": True,
            "state": "available",
            "name": "Tamtaro Complete SEL Setup",
            "installed_version": "3.1.3",
            "latest_version": "3.2.2",
            "update_available": True,
            "requires_browser_unlock": self.legacy,
            "message": (
                "Tamtaro 3.2.2 is available. "
                "AIOStreams 2.33 needs one browser unlock before applying it."
                if self.legacy
                else "Tamtaro 3.2.2 is available."
            ),
        }

    def link(self, base_url, uuid, password):

        self.links.append(
            (base_url, uuid, password)
        )

        return {
            "applied_version": "3.1.3",
        }

    def unlink(self, base_url):

        self.unlinks += 1
        assert base_url == "http://localhost:3500"

    def update_launch(self, base_url, browser_host):

        self.launches.append(
            (base_url, browser_host)
        )

        result = {
            "target": (
                "http://localhost:3500/stremio/configure"
                "?templateId=tamtaro.complete"
            ),
            "auth_mode": (
                "password"
                if self.legacy
                else "session"
            ),
        }

        if not self.legacy:
            result.update(
                {
                    "session_token": (
                        "secret-session-token"
                    ),
                    "expires_at": 4102444800000,
                }
            )

        return result


original_service_status = routes.service_status
original_stremio = routes.stremio_controller
original_templates = (
    routes.aiostreams_template_updates
)

try:
    templates = TestTemplateUpdates()
    routes.service_status = TestServiceStatus()
    routes.stremio_controller = (
        TestStremioController()
    )
    routes.aiostreams_template_updates = templates

    client = OrionAPIServer().app.test_client()

    page_response = client.get(
        "/services/aiostreams"
    )
    page = page_response.get_data(
        as_text=True
    )

    assert page_response.status_code == 200
    assert "Template updates" in page
    assert "Tamtaro 3.2.2 is available." in page
    assert "3.1.3" in page
    assert "3.2.2" in page
    assert "Update template" in page
    assert routes.template_update_token in page

    forbidden = client.post(
        "/services/aiostreams/template/update"
    )
    assert forbidden.status_code == 403

    link_response = client.post(
        "/services/aiostreams/template/link",
        data={
            "token": routes.template_update_token,
            "uuid": (
                "12345678-1234-1234-1234-"
                "123456789abc"
            ),
            "password": "temporary-password",
        },
    )

    assert link_response.status_code == 302
    assert len(templates.links) == 1
    assert "temporary-password" not in (
        link_response.headers["Location"]
    )

    update_response = client.post(
        "/services/aiostreams/template/update",
        data={
            "token": routes.template_update_token,
        },
    )

    assert update_response.status_code == 302
    assert update_response.headers[
        "Location"
    ].startswith("http://localhost:3500/")
    assert templates.launches == [
        ("http://localhost:3500", "localhost")
    ]

    cookies = update_response.headers.getlist(
        "Set-Cookie"
    )

    assert any(
        "aiostreams.config-session="
        "secret-session-token" in cookie
        and "HttpOnly" in cookie
        and "Path=/api" in cookie
        for cookie in cookies
    )
    assert any(
        "aiostreams.has-config-session=1"
        in cookie
        and "Path=/" in cookie
        for cookie in cookies
    )

    templates.legacy = True
    legacy_response = client.post(
        "/services/aiostreams/template/update",
        data={
            "token": routes.template_update_token,
        },
    )

    assert legacy_response.status_code == 302
    assert not legacy_response.headers.getlist(
        "Set-Cookie"
    )

    legacy_page = client.get(
        "/services/aiostreams"
    ).get_data(as_text=True)
    assert "Prepare update" in legacy_page
    assert "Use This Template Now" in legacy_page
    assert "existing services" in legacy_page

    unlink_response = client.post(
        "/services/aiostreams/template/unlink",
        data={
            "token": routes.template_update_token,
        },
    )

    assert unlink_response.status_code == 302
    assert templates.unlinks == 1

    print("✓ Template status displayed")
    print("✓ Link and update routes secured")
    print("✓ Password excluded from redirects")
    print("✓ AIOStreams session relayed securely")

finally:
    routes.service_status = original_service_status
    routes.stremio_controller = original_stremio
    routes.aiostreams_template_updates = (
        original_templates
    )

print()
print("✓ AIOStreams template route test passed")
