import json
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit

import requests

from app.api.aiostreams_templates import (
    AIOStreamsTemplateUpdates,
    TemplateUpdateError,
)


print("=" * 60)
print("AIOSTREAMS TEMPLATE UPDATE TEST")
print("=" * 60)
print()


UUID = "12345678-1234-1234-1234-123456789abc"
PASSWORD = "one-time-password"
SESSION_TOKEN = "remembered-session-token"


class TestProtector:

    def protect(self, value):

        return b"protected:" + value[::-1]

    def unprotect(self, value):

        if not value.startswith(b"protected:"):
            raise ValueError("not protected")

        return value[len(b"protected:") :][::-1]


class TestCookies(dict):

    def get(self, name, default=None, **_kwargs):

        return super().get(name, default)


class TestResponse:

    def __init__(
        self,
        payload=None,
        status=200,
        url="http://localhost/",
        headers=None,
        cookies=None,
        raw=None,
    ):

        self.payload = payload
        self.status_code = status
        self.url = url
        self.headers = headers or {}
        self.cookies = TestCookies(
            cookies or {}
        )
        self.raw = raw

    def raise_for_status(self):

        if self.status_code >= 400:
            error = requests.HTTPError(
                f"HTTP {self.status_code}"
            )
            error.response = self
            raise error

    def json(self):

        return self.payload

    def iter_content(self, _size):

        raw = self.raw

        if raw is None:
            raw = json.dumps(
                self.payload
            ).encode("utf-8")

        yield raw


class TestSession:

    def __init__(
        self,
        requests_log,
        legacy=False,
    ):

        self.requests_log = requests_log
        self.cookies = TestCookies()
        self.legacy = legacy

    def get(self, url, **kwargs):

        self.requests_log.append(
            ("GET", url, kwargs)
        )

        if "raw.githubusercontent.com" in url:
            payload = {
                "metadata": {
                    "id": "tamtaro.complete",
                    "name": "Tamtaro Complete SEL Setup",
                    "version": "3.2.2",
                },
                "config": {},
            }

            return TestResponse(
                payload=payload,
                url=url,
            )

        if url.endswith("/api/v1/user"):
            return TestResponse(
                payload={
                    "data": {
                        "encryptedPassword": (
                            "encrypted-config-token"
                        ),
                        "userData": {
                            "appliedTemplates": [
                                {
                                    "id": "tamtaro.complete",
                                    "version": "3.1.3",
                                }
                            ]
                        }
                    }
                },
                url=url,
            )

        raise AssertionError(
            f"Unexpected GET {url}"
        )

    def post(self, url, **kwargs):

        self.requests_log.append(
            ("POST", url, kwargs)
        )

        if url.endswith("/api/v1/user/session"):
            if self.legacy:
                return TestResponse(
                    payload={"error": "not found"},
                    status=404,
                    url=url,
                )

            self.cookies[
                "aiostreams.config-session"
            ] = SESSION_TOKEN

            return TestResponse(
                payload={
                    "data": {
                        "expiresAt": 4102444800000,
                    }
                },
                url=url,
            )

        raise AssertionError(
            f"Unexpected POST {url}"
        )

    def close(self):

        return None


with TemporaryDirectory() as temporary:

    requests_log = []

    manager = AIOStreamsTemplateUpdates(
        state_path=(
            f"{temporary}/template-session.json"
        ),
        protector=TestProtector(),
        session_factory=(
            lambda: TestSession(requests_log)
        ),
        clock=lambda: 1000,
    )

    state = manager.link(
        "http://localhost:3500",
        UUID,
        PASSWORD,
    )

    assert state["uuid"] == UUID
    assert state["auth_mode"] == "session"
    assert state["session_token"] == SESSION_TOKEN
    assert state["applied_version"] == "3.1.3"

    state_text = manager.state_path.read_text(
        encoding="utf-8"
    )

    assert PASSWORD not in state_text
    assert SESSION_TOKEN not in state_text

    config_request = next(
        request
        for request in requests_log
        if request[0] == "GET"
        and request[1].endswith("/api/v1/user")
    )

    assert config_request[2]["auth"] == (
        UUID,
        PASSWORD,
    )

    status = manager.status(
        "http://localhost:3500"
    )

    assert status["linked"] is True
    assert status["installed_version"] == "3.1.3"
    assert status["latest_version"] == "3.2.2"
    assert status["update_available"] is True
    assert status["state"] == "available"

    launch = manager.update_launch(
        "http://localhost:3500",
        "127.0.0.1",
    )

    parsed = urlsplit(launch["target"])
    query = parse_qs(parsed.query)

    assert parsed.netloc == "127.0.0.1:3500"
    assert parsed.path == "/stremio/configure"
    assert query["templateId"] == [
        "tamtaro.complete"
    ]
    assert query["template"] == [
        manager.TEMPLATE_URL
    ]
    assert launch["session_token"] == SESSION_TOKEN

    manager.unlink()
    assert not manager.state_path.exists()

    print("✓ One-time password was never stored")
    print("✓ Linked template version detected")
    print("✓ Newer Tamtaro version detected")
    print("✓ Authenticated update launch prepared")


with TemporaryDirectory() as temporary:

    legacy_log = []
    legacy_manager = AIOStreamsTemplateUpdates(
        state_path=(
            f"{temporary}/legacy-session.json"
        ),
        protector=TestProtector(),
        session_factory=(
            lambda: TestSession(
                legacy_log,
                legacy=True,
            )
        ),
        clock=lambda: 1000,
    )

    legacy_state = legacy_manager.link(
        "http://localhost:3500",
        UUID,
        PASSWORD,
    )

    assert legacy_state["auth_mode"] == "password"
    assert legacy_state["password"] == PASSWORD

    legacy_text = (
        legacy_manager.state_path.read_text(
            encoding="utf-8"
        )
    )

    assert PASSWORD not in legacy_text

    legacy_status = legacy_manager.status(
        "http://localhost:3500",
        force=True,
    )

    assert legacy_status["update_available"] is True
    assert legacy_status["auth_mode"] == "password"
    assert legacy_status["requires_browser_unlock"] is True
    assert "one browser unlock" in legacy_status["message"]

    legacy_launch = legacy_manager.update_launch(
        "http://localhost:3500",
        "localhost",
    )

    legacy_url = urlsplit(
        legacy_launch["target"]
    )

    assert legacy_launch["auth_mode"] == "password"
    assert "session_token" not in legacy_launch
    assert legacy_url.path.startswith(
        f"/stremio/{UUID}/"
    )
    assert legacy_url.path.endswith("/configure")
    assert PASSWORD not in legacy_launch["target"]

    print("✓ AIOStreams 2.33.x fallback supported")
    print("✓ Legacy password stored only with Windows protection")


invalid_manager = AIOStreamsTemplateUpdates(
    state_path="unused.json",
    protector=TestProtector(),
    session_factory=lambda: TestSession([]),
)

try:
    invalid_manager.link(
        "http://example.com:3500",
        UUID,
        PASSWORD,
    )
    raise AssertionError(
        "Remote AIOStreams address was accepted"
    )
except TemplateUpdateError:
    pass

try:
    invalid_manager.link(
        "http://localhost:3500",
        "not-a-uuid",
        PASSWORD,
    )
    raise AssertionError(
        "Invalid UUID was accepted"
    )
except TemplateUpdateError:
    pass

print("✓ Remote targets and invalid UUIDs rejected")
print()
print("✓ AIOStreams template update test passed")
