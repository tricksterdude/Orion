import ipaddress
import re
import socket
import time

from app.receivers.base import (
    ReceiverAdapter,
    ReceiverConfigurationError,
    ReceiverUnavailableError,
)
from app.receivers.models import (
    ReceiverCapabilities,
    ReceiverStatus,
)


class DenonMarantzReceiver(ReceiverAdapter):

    adapter_id = "denon_marantz"
    adapter_name = "Denon / Marantz"
    DEFAULT_PORT = 23
    QUERY_INTERVAL = 0.05
    HOST_PATTERN = re.compile(
        r"^(?=.{1,253}$)(?!-)(?:[A-Za-z0-9-]{1,63}\.)*"
        r"[A-Za-z0-9][A-Za-z0-9-]{0,62}$"
    )
    CAPABILITIES = ReceiverCapabilities(
        power=True,
        selected_input=True,
        volume=True,
        mute=True,
        sound_mode=True,
        signal_format=False,
        control=False,
    )
    QUERIES = (
        "PW?",
        "SI?",
        "MV?",
        "MU?",
        "MS?",
    )

    def __init__(
        self,
        host,
        port=DEFAULT_PORT,
        timeout=0.75,
        connection_factory=None,
        sleeper=None,
    ):

        self.host = self.validate_host(host)

        try:

            self.port = int(port)

        except (TypeError, ValueError):

            raise ReceiverConfigurationError(
                "The receiver port is invalid."
            )

        if not 1 <= self.port <= 65535:

            raise ReceiverConfigurationError(
                "The receiver port is invalid."
            )

        self.timeout = float(timeout)
        self.connection_factory = (
            connection_factory or socket.create_connection
        )
        self.sleeper = sleeper or time.sleep

    @classmethod
    def validate_host(cls, value):

        host = str(value or "").strip()

        if not host or any(
            character in host
            for character in "/\\?#@"
        ):

            raise ReceiverConfigurationError(
                "Enter only the receiver's IP address or host name."
            )

        try:

            address = ipaddress.ip_address(host)

            if not (
                address.is_private
                or address.is_loopback
                or address.is_link_local
            ):

                raise ReceiverConfigurationError(
                    "The receiver must use a local network address."
                )

            return host

        except ValueError:

            pass

        if not cls.HOST_PATTERN.fullmatch(host):

            raise ReceiverConfigurationError(
                "The receiver address is invalid."
            )

        local_name = (
            "." not in host
            or host.casefold().endswith(
                (
                    ".local",
                    ".lan",
                    ".home",
                    ".home.arpa",
                    ".internal",
                )
            )
        )

        if not local_name:

            raise ReceiverConfigurationError(
                "The receiver must use a local network host name."
            )

        return host

    @staticmethod
    def _volume(value):

        raw = str(value or "").strip()

        if not raw.isdigit() or len(raw) not in {2, 3}:

            return None

        level = (
            float(raw) / 10
            if len(raw) == 3
            else float(raw)
        )

        return round(level - 80, 1)

    @staticmethod
    def _responses(payload):

        responses = {}

        for line in payload.replace("\n", "\r").split("\r"):

            line = line.strip()

            if not line:

                continue

            for prefix in ("PW", "SI", "MV", "MU", "MS"):

                if line.startswith(prefix) and len(line) > len(prefix):

                    value = line[len(prefix):].strip()

                    if prefix == "PW" and value not in {
                        "ON",
                        "STANDBY",
                    }:

                        continue

                    if prefix == "MU" and value not in {
                        "ON",
                        "OFF",
                    }:

                        continue

                    if prefix == "MV" and not (
                        value.isdigit()
                        and len(value) in {2, 3}
                    ):

                        continue

                    if value == "?":

                        continue

                    responses[prefix] = value
                    break

        return responses

    def _query(self):

        try:

            connection = self.connection_factory(
                (self.host, self.port),
                timeout=self.timeout,
            )

            with connection:

                if hasattr(connection, "settimeout"):

                    connection.settimeout(self.timeout)

                for index, query in enumerate(self.QUERIES):

                    connection.sendall(
                        (query + "\r").encode("ascii")
                    )

                    if index + 1 < len(self.QUERIES):

                        self.sleeper(self.QUERY_INTERVAL)

                chunks = []

                while True:

                    try:

                        chunk = connection.recv(4096)

                    except socket.timeout:

                        break

                    if not chunk:

                        break

                    chunks.append(chunk)

                    if all(
                        prefix in self._responses(
                            b"".join(chunks).decode(
                                "ascii",
                                errors="ignore",
                            )
                        )
                        for prefix in (
                            "PW",
                            "SI",
                            "MV",
                            "MU",
                            "MS",
                        )
                    ):

                        break

        except (OSError, ValueError, TypeError) as error:

            raise ReceiverUnavailableError(
                "The receiver did not answer Orion's read-only status request."
            ) from error

        return self._responses(
            b"".join(chunks).decode(
                "ascii",
                errors="ignore",
            )
        )

    def status(self):

        responses = self._query()

        if not responses:

            raise ReceiverUnavailableError(
                "The receiver returned no readable status."
            )

        power = responses.get("PW")
        muted = responses.get("MU")

        return ReceiverStatus(
            adapter=self.adapter_id,
            name=self.adapter_name,
            host=self.host,
            available=True,
            capabilities=self.CAPABILITIES,
            power=(
                "on"
                if power == "ON"
                else "standby"
                if power == "STANDBY"
                else power.casefold()
                if power
                else None
            ),
            selected_input=responses.get("SI"),
            volume_db=self._volume(responses.get("MV")),
            muted=(
                muted == "ON"
                if muted in {"ON", "OFF"}
                else None
            ),
            sound_mode=responses.get("MS"),
        )
