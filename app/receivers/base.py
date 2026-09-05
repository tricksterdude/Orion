from abc import ABC, abstractmethod


class ReceiverError(RuntimeError):
    pass


class ReceiverConfigurationError(ReceiverError):
    pass


class ReceiverUnavailableError(ReceiverError):
    pass


class ReceiverAdapter(ABC):

    adapter_id = "unknown"
    adapter_name = "Unknown receiver"

    @abstractmethod
    def status(self):

        raise NotImplementedError
