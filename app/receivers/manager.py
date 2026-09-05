from app.local_configuration import local_configuration
from app.receivers.base import (
    ReceiverConfigurationError,
    ReceiverUnavailableError,
)
from app.receivers.denon_marantz import DenonMarantzReceiver


class ReceiverManager:

    ADAPTERS = {
        DenonMarantzReceiver.adapter_id: DenonMarantzReceiver,
    }

    def __init__(
        self,
        configuration=None,
        adapter_factories=None,
    ):

        self.configuration = (
            configuration or local_configuration
        )
        self.adapter_factories = (
            adapter_factories or self.ADAPTERS
        )

    @classmethod
    def options(cls):

        return [
            {
                "id": adapter_id,
                "name": adapter.adapter_name,
            }
            for adapter_id, adapter in cls.ADAPTERS.items()
        ]

    @classmethod
    def validate_configuration(cls, adapter_id, host):

        selected = str(adapter_id or "none").strip()
        address = str(host or "").strip()

        if selected == "none":

            return "none", ""

        factory = cls.ADAPTERS.get(selected)

        if factory is None:

            raise ReceiverConfigurationError(
                "The selected receiver family is not supported."
            )

        return selected, factory.validate_host(address)

    def configured(self):

        try:

            media = self.configuration.read("media")
            audio = media.get("audio") or {}

        except Exception:

            return None

        adapter_id, host = self.validate_configuration(
            audio.get("receiver_adapter"),
            audio.get("receiver_host"),
        )

        if adapter_id == "none":

            return None

        factory = self.adapter_factories.get(adapter_id)

        if factory is None:

            raise ReceiverConfigurationError(
                "The configured receiver family is not supported."
            )

        return factory(host)

    def observe(self, request=None):

        try:

            adapter = self.configured()

            if adapter is None:

                return None

            result = adapter.status().as_dict()

        except (ReceiverConfigurationError, ReceiverUnavailableError) as error:

            return {
                "available": False,
                "error": str(error),
            }

        expected = str(
            getattr(request, "immersive_audio", None) or ""
        ).strip()
        observed = str(
            result.get("sound_mode") or ""
        ).strip()
        matches = None

        if expected and observed:

            expected_marker = (
                "ATMOS"
                if expected == "Dolby Atmos"
                else "DTS:X"
                if expected == "DTS:X"
                else ""
            )

            if expected_marker:

                matches = expected_marker in observed.upper()

        result["expected_immersive_audio"] = expected or None
        result["matches_expected_audio"] = matches

        return result
