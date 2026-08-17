from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayMode:
    width: int
    height: int
    refresh: int
    bits: int