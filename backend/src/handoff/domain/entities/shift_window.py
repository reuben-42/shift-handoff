from collections.abc import Iterator
from dataclasses import dataclass

from handoff.domain.entities.records import (
    Incident,
    MedAdministration,
    Note,
    Order,
    SourceRecord,
    VitalSign,
)
from handoff.domain.entities.resident import Resident
from handoff.domain.entities.shift import Shift
from handoff.domain.value_objects import SourceId


@dataclass(frozen=True)
class ShiftWindow:
    """One resident's records inside one shift: the evidence a handoff may cite."""

    resident: Resident
    shift: Shift
    notes: tuple[Note, ...] = ()
    vitals: tuple[VitalSign, ...] = ()
    meds: tuple[MedAdministration, ...] = ()
    orders: tuple[Order, ...] = ()
    incidents: tuple[Incident, ...] = ()

    def __post_init__(self) -> None:
        for record in self.records():
            if record.resident_id != self.resident.id:
                raise ValueError(
                    f"{record.id} belongs to {record.resident_id}, not {self.resident.id}"
                )
            if not self.shift.contains(record.time):
                raise ValueError(f"{record.id} at {record.time} is outside shift {self.shift.id}")

    def records(self) -> Iterator[SourceRecord]:
        yield from self.notes
        yield from self.vitals
        yield from self.meds
        yield from self.orders
        yield from self.incidents

    def chronological(self) -> list[SourceRecord]:
        return sorted(self.records(), key=lambda r: (r.time, r.id.value))

    @property
    def source_ids(self) -> frozenset[SourceId]:
        return frozenset(r.id for r in self.records())

    def find(self, source_id: SourceId) -> SourceRecord | None:
        return next((r for r in self.records() if r.id == source_id), None)
