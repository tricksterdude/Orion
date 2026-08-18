from types import SimpleNamespace

from app.api.service_status import ServiceStatus


class FakeServiceManager:

    def get_all(self):

        return [
            SimpleNamespace(
                name="AIOStreams",
                port=3500,
                url="http://localhost:3500",
            ),
            SimpleNamespace(
                name="NZBDAV",
                port=8500,
                url="http://localhost:8500",
            ),
        ]


class FakeHealthManager:

    def check(self, url):

        if url.endswith("3500"):

            return {
                "healthy": True,
                "status_code": 200,
                "response_time": 14.2,
            }

        return {
            "healthy": False,
            "status_code": None,
            "response_time": None,
        }


print("=" * 60)
print("SERVICE STATUS TEST")
print("=" * 60)
print()

status = ServiceStatus(
    service_manager=FakeServiceManager(),
    health_manager=FakeHealthManager(),
)

services = status.get_all()

assert len(services) == 2

print("✓ All configured services checked")

aiostreams = services[0]

assert aiostreams["name"] == "AIOStreams"
assert aiostreams["port"] == 3500
assert aiostreams["healthy"] is True
assert aiostreams["status_code"] == 200
assert aiostreams["response_time"] == 14.2

print("✓ Healthy service result returned")

nzbdav = services[1]

assert nzbdav["name"] == "NZBDAV"
assert nzbdav["port"] == 8500
assert nzbdav["healthy"] is False
assert nzbdav["status_code"] is None
assert nzbdav["response_time"] is None

print("✓ Offline service result returned")

print()
print("✓ Service status test passed")