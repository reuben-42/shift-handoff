"""Source records: what the chart already holds. Each one has a citable SourceId.

Times are naive datetimes on the unit's local clock.
"""

from dataclasses import dataclass
from datetime import datetime

from handoff.domain.value_objects import MedStatus, SourceId, SourceKind


def _check_kind(source_id: SourceId, expected: SourceKind, record: str) -> None:
    if source_id.kind != expected:
        raise ValueError(f"{record} IDs must start with {expected.value}, got {source_id}")


@dataclass(frozen=True)
class Note:
    id: SourceId
    resident_id: str
    time: datetime
    author_role: str
    text: str

    def __post_init__(self) -> None:
        _check_kind(self.id, SourceKind.NOTE, "Note")


@dataclass(frozen=True)
class VitalSign:
    id: SourceId
    resident_id: str
    time: datetime
    bp_sys: int | None = None
    bp_dia: int | None = None
    hr: int | None = None
    temp_c: float | None = None
    rr: int | None = None
    spo2: int | None = None
    pain_0_10: int | None = None
    weight_kg: float | None = None

    def __post_init__(self) -> None:
        _check_kind(self.id, SourceKind.VITAL, "Vital sign")
        if self.pain_0_10 is not None and not 0 <= self.pain_0_10 <= 10:
            raise ValueError("Pain score must be 0-10")
        if self.spo2 is not None and not 0 <= self.spo2 <= 100:
            raise ValueError("SpO2 must be 0-100")


@dataclass(frozen=True)
class MedAdministration:
    id: SourceId
    resident_id: str
    time: datetime
    med: str
    dose: str
    status: MedStatus
    reason: str | None = None

    def __post_init__(self) -> None:
        _check_kind(self.id, SourceKind.MED, "Med administration")


@dataclass(frozen=True)
class Order:
    id: SourceId
    resident_id: str
    time: datetime
    type: str
    text: str

    def __post_init__(self) -> None:
        _check_kind(self.id, SourceKind.ORDER, "Order")


@dataclass(frozen=True)
class Incident:
    id: SourceId
    resident_id: str
    time: datetime
    type: str
    text: str

    def __post_init__(self) -> None:
        _check_kind(self.id, SourceKind.INCIDENT, "Incident")


SourceRecord = Note | VitalSign | MedAdministration | Order | Incident
