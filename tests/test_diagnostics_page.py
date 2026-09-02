from app.api import routes
from app.api.server import OrionAPIServer


print("=" * 60)
print("ORION DIAGNOSTICS PAGE TEST")
print("=" * 60)
print()


SNAPSHOT = {
    "status": "warning",
    "label": "Warning",
    "generated_at": "2026-09-02T12:00:00+00:00",
    "counts": {
        "healthy": 5,
        "warning": 1,
        "action_required": 1,
    },
    "checks": [
        {
            "id": "docker",
            "name": "Docker engine",
            "status": "healthy",
            "label": "Healthy",
            "summary": "Docker Desktop is available to Orion.",
            "guidance": "No action is required.",
            "detail": None,
        },
        {
            "id": "services",
            "name": "Configured services",
            "status": "warning",
            "label": "Warning",
            "summary": "Three of four services are responding.",
            "guidance": "Open the affected service page.",
            "detail": "One service needs attention.",
        },
        {
            "id": "ffprobe",
            "name": "Playback analysis",
            "status": "action_required",
            "label": "Action required",
            "summary": "FFprobe is unavailable.",
            "guidance": "Install FFmpeg, then restart Orion.",
            "detail": None,
        },
    ],
}


class FakeDiagnostics:

    def __init__(self):

        self.calls = []

    def run(self, services=None, force=False):

        self.calls.append(
            {
                "services": services,
                "force": force,
            }
        )

        return SNAPSHOT

    def report(self, snapshot):

        assert snapshot is SNAPSHOT

        return (
            "ORION SAFE DIAGNOSTIC REPORT\n"
            "Overall status: Warning\n"
            "No private values included.\n"
        )


original_diagnostics = routes.system_diagnostics
original_service_get_all = routes.service_status.get_all

try:

    fake_diagnostics = FakeDiagnostics()
    routes.system_diagnostics = fake_diagnostics
    routes.service_status.get_all = lambda: [
        {
            "name": "AIOStreams",
            "healthy": True,
        }
    ]

    server = OrionAPIServer()
    client = server.app.test_client()

    response = client.get("/diagnostics")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Health &amp; Diagnostics" in page
    assert "Know Orion is ready before playback." in page
    assert "Overall state" in page
    assert "Warning" in page
    assert "Docker engine" in page
    assert "Configured services" in page
    assert "Playback analysis" in page
    assert "What to do:" in page
    assert "Copy safe report" in page
    assert "Download safe report" in page
    assert "ORION SAFE DIAGNOSTIC REPORT" in page
    assert 'href="/diagnostics?refresh=1"' in page
    assert 'href="/diagnostics/report"' in page
    assert "navigator.clipboard.writeText" in page

    print("✓ Diagnostics page explains every system check")
    print("✓ Refresh, copy and download actions are displayed")

    refresh_response = client.get(
        "/diagnostics?refresh=1"
    )

    assert refresh_response.status_code == 200
    assert fake_diagnostics.calls[-1]["force"] is True

    print("✓ User can explicitly refresh diagnostics")

    report_response = client.get(
        "/diagnostics/report"
    )
    report = report_response.get_data(
        as_text=True
    )

    assert report_response.status_code == 200
    assert report_response.mimetype == "text/plain"
    assert (
        report_response.headers["Content-Disposition"]
        == "attachment; filename=orion-diagnostics.txt"
    )
    assert (
        report_response.headers["Cache-Control"]
        == "no-store"
    )
    assert (
        report_response.headers["X-Content-Type-Options"]
        == "nosniff"
    )
    assert "ORION SAFE DIAGNOSTIC REPORT" in report

    print("✓ Safe report downloads without browser caching")

finally:

    routes.system_diagnostics = original_diagnostics
    routes.service_status.get_all = original_service_get_all

print()
print("✓ Orion diagnostics page test passed")
