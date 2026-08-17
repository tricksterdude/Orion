from types import SimpleNamespace
from unittest.mock import patch

import psutil

from app.providers.playback.usenetstreamer import (
    UsenetStreamerPlaybackProvider,
)


class ImmediateEvent:

    def is_set(self):

        return False

    def wait(self, timeout):

        return False


class TestProvider(
    UsenetStreamerPlaybackProvider
):

    CONNECTION_GRACE_SECONDS = 0
    CONNECTION_START_TIMEOUT = 1

    def __init__(self, on_stopped):

        super().__init__(
            session=object(),
            on_stopped=on_stopped,
        )

        self._connection_states = iter(
            [True, False]
        )

        self._stop_event = ImmediateEvent()

    def _has_stream_connection(self):

        return next(
            self._connection_states
        )


print("=" * 60)
print("USENETSTREAMER STOP DETECTION TEST")
print("=" * 60)
print()

outbound_connection = SimpleNamespace(
    status=psutil.CONN_ESTABLISHED,
    laddr=SimpleNamespace(port=51000),
    raddr=SimpleNamespace(port=7001),
)

provider = UsenetStreamerPlaybackProvider(
    session=object()
)

with patch(
    "psutil.net_connections",
    return_value=[outbound_connection],
):

    assert (
        provider._has_stream_connection()
        is True
    )

print(
    "✓ Stremio-to-7001 connection detected"
)

mirrored_server_connection = SimpleNamespace(
    status=psutil.CONN_ESTABLISHED,
    laddr=SimpleNamespace(port=7001),
    raddr=SimpleNamespace(port=51000),
)

with patch(
    "psutil.net_connections",
    return_value=[
        mirrored_server_connection
    ],
):

    assert (
        provider._has_stream_connection()
        is False
    )

print(
    "✓ Mirrored server connection ignored"
)

closed_connection = SimpleNamespace(
    status=psutil.CONN_CLOSE,
    laddr=SimpleNamespace(port=51000),
    raddr=SimpleNamespace(port=7001),
)

with patch(
    "psutil.net_connections",
    return_value=[closed_connection],
):

    assert (
        provider._has_stream_connection()
        is False
    )

print("✓ Closed connection ignored")

stop_events = []

test_provider = TestProvider(
    on_stopped=lambda: stop_events.append(
        "stopped"
    )
)

test_provider._monitor_connection()

assert stop_events == ["stopped"]

print("✓ Playback stop callback sent")
print()
print(
    "✓ UsenetStreamer stop detection "
    "test passed"
)