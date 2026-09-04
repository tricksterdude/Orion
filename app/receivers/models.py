from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ReceiverCapabilities:

    power: bool = False
    selected_input: bool = False
    volume: bool = False
    mute: bool = False
    sound_mode: bool = False
    signal_format: bool = False
    control: bool = False

    def as_dict(self):

        return asdict(self)


@dataclass(frozen=True)
class ReceiverStatus:

    adapter: str
    name: str
    host: str
    available: bool
    capabilities: ReceiverCapabilities
    power: str | None = None
    selected_input: str | None = None
    volume_db: float | None = None
    muted: bool | None = None
    sound_mode: str | None = None
    signal_format: str | None = None
    error: str | None = None

    def as_dict(self):

        document = asdict(self)
        document["capabilities"] = (
            self.capabilities.as_dict()
        )
        return document
