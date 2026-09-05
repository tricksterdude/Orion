from types import SimpleNamespace

from app.receivers.base import (
    ReceiverConfigurationError,
    ReceiverUnavailableError,
)
from app.receivers.denon_marantz import DenonMarantzReceiver
from app.receivers.manager import ReceiverManager


print("=" * 60)
print("AV RECEIVER OBSERVATION TEST")
print("=" * 60)
print()


class FakeConnection:

    def __init__(self, response):

        self.response = response
        self.sent = []

    def __enter__(self):

        return self

    def __exit__(self, *arguments):

        return False

    def settimeout(self, timeout):

        self.timeout = timeout

    def sendall(self, payload):

        self.sent.append(payload)

    def recv(self, size):

        if self.response is None:

            return b""

        response = self.response
        self.response = None
        return response


connection = FakeConnection(
    b"PWON\rSIGAME\rMV405\rMVMAX 98\rMUOFF\rMSDOLBY ATMOS\r"
)
addresses = []


def connect(address, timeout):

    addresses.append((address, timeout))
    return connection


receiver = DenonMarantzReceiver(
    "192.168.1.50",
    connection_factory=connect,
    sleeper=lambda seconds: None,
)
status = receiver.status()

assert addresses == [(("192.168.1.50", 23), 0.75)]
assert connection.sent == [
    b"PW?\r",
    b"SI?\r",
    b"MV?\r",
    b"MU?\r",
    b"MS?\r",
]
assert status.available is True
assert status.power == "on"
assert status.selected_input == "GAME"
assert status.volume_db == -39.5
assert status.muted is False
assert status.sound_mode == "DOLBY ATMOS"
assert status.capabilities.control is False

print("✓ Denon/Marantz status read through the documented protocol")


for invalid_host in (
    "",
    "http://receiver.local",
    "receiver.local/path",
    "bad host",
    "example.com",
    "8.8.8.8",
):

    try:

        DenonMarantzReceiver(invalid_host)

    except ReceiverConfigurationError:

        pass

    else:

        raise AssertionError(
            f"Invalid receiver host accepted: {invalid_host}"
        )

print("✓ Unsafe receiver addresses rejected")


def unavailable(address, timeout):

    raise OSError("Receiver offline")


try:

    DenonMarantzReceiver(
        "192.168.1.50",
        connection_factory=unavailable,
    ).status()

except ReceiverUnavailableError as error:

    assert "read-only status request" in str(error)

else:

    raise AssertionError("An offline receiver did not fail safely")

print("✓ Network failures remain harmless")


class FakeConfiguration:

    def __init__(self, adapter="denon_marantz", host="receiver.local"):

        self.adapter = adapter
        self.host = host

    def read(self, kind):

        assert kind == "media"

        return {
            "audio": {
                "receiver_adapter": self.adapter,
                "receiver_host": self.host,
            }
        }


class FakeAdapter:

    adapter_name = "Fake receiver"

    def __init__(self, host):

        self.host = host

    @staticmethod
    def validate_host(host):

        return str(host)

    def status(self):

        return SimpleNamespace(
            as_dict=lambda: {
                "adapter": "denon_marantz",
                "name": self.adapter_name,
                "host": self.host,
                "available": True,
                "sound_mode": "DTS:X",
            }
        )


manager = ReceiverManager(
    configuration=FakeConfiguration(),
    adapter_factories={"denon_marantz": FakeAdapter},
)
matching = manager.observe(
    SimpleNamespace(immersive_audio="DTS:X")
)
mismatch = manager.observe(
    SimpleNamespace(immersive_audio="Dolby Atmos")
)

assert matching["matches_expected_audio"] is True
assert mismatch["matches_expected_audio"] is False

disabled = ReceiverManager(
    configuration=FakeConfiguration(adapter="none", host=""),
).observe()

assert disabled is None

print("✓ Expected immersive audio compared with receiver sound mode")
print("✓ Unconfigured receiver monitoring remains disabled")
print()
print("✓ AV receiver observation test passed")
