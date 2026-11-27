"""Read ports for the chart. Kept small (interface segregation)."""

from datetime import date, datetime
from typing import Protocol

from handoff.domain.entities import Resident, Shift, ShiftWindow, SourceRecord, VitalSign
from handoff.domain.value_objects import SourceId


class ResidentReader(Protocol):
    def list_residents(self) -> list[Resident]: ...

    def get(self, resident_id: str) -> Resident | None: ...


class ShiftReader(Protocol):
    def date_range(self) -> tuple[date, date] | None:
        """First and last dates that have chart data, or None if the chart is empty."""
        ...


class ClinicalRecordReader(Protocol):
    def window(self, resident: Resident, shift: Shift) -> ShiftWindow:
        """Every record for this resident with a time inside the shift."""
        ...

    def vitals_before(self, resident_id: str, before: datetime, days: int) -> list[VitalSign]:
        """Vitals in the `days` days before `before` (for baselines)."""
        ...

    def get_source(self, source_id: SourceId) -> SourceRecord | None: ...
