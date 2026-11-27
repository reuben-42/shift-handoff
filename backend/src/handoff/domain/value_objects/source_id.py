"""SourceId: the record ID a claim cites. Its letter prefix says what kind of record it is."""

import re
from dataclasses import dataclass
from enum import StrEnum

_PATTERN = re.compile(r"^([NVMOI])(\d+)$")


class SourceKind(StrEnum):
    NOTE = "N"
    VITAL = "V"
    MED = "M"
    ORDER = "O"
    INCIDENT = "I"


@dataclass(frozen=True, order=True)
class SourceId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _PATTERN.match(self.value):
            raise ValueError(
                f"Invalid source ID {self.value!r}: expected N/V/M/O/I followed by digits"
            )

    @property
    def kind(self) -> SourceKind:
        return SourceKind(self.value[0])

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return isinstance(value, str) and bool(_PATTERN.match(value))

    def __str__(self) -> str:
        return self.value
