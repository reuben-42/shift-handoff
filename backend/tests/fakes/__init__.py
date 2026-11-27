"""In-memory fakes for application tests: no database, no network."""

from datetime import date, datetime, timedelta

from handoff.domain.entities import (
    ChangeClaim,
    Claim,
    EvidencePack,
    Handoff,
    HandoffDraft,
    Incident,
    MedAdministration,
    Note,
    Order,
    Resident,
    Sbar,
    Shift,
    ShiftWindow,
    SourceRecord,
    VitalSign,
)
from handoff.domain.value_objects import ShiftPattern, SourceId, SourceKind


class InMemoryResidentReader:
    def __init__(self, residents: list[Resident]):
        self._residents = {r.id: r for r in residents}

    def list_residents(self) -> list[Resident]:
        return list(self._residents.values())

    def get(self, resident_id: str) -> Resident | None:
        return self._residents.get(resident_id)


class InMemoryClinicalRecordReader:
    """Also implements ShiftReader."""

    def __init__(self, records: list[SourceRecord]):
        self._records = list(records)

    def window(self, resident: Resident, shift: Shift) -> ShiftWindow:
        mine = [r for r in self._records if r.resident_id == resident.id and shift.contains(r.time)]

        def of(kind: type) -> tuple:
            return tuple(r for r in mine if isinstance(r, kind))

        return ShiftWindow(
            resident, shift, of(Note), of(VitalSign), of(MedAdministration), of(Order), of(Incident)
        )

    def vitals_before(self, resident_id: str, before: datetime, days: int) -> list[VitalSign]:
        since = before - timedelta(days=days)
        return [
            r
            for r in self._records
            if isinstance(r, VitalSign)
            and r.resident_id == resident_id
            and since <= r.time < before
        ]

    def get_source(self, source_id: SourceId) -> SourceRecord | None:
        return next((r for r in self._records if r.id == source_id), None)

    def date_range(self) -> tuple[date, date] | None:
        if not self._records:
            return None
        times = [r.time for r in self._records]
        return min(times).date(), max(times).date()


class InMemoryHandoffStore:
    def __init__(self) -> None:
        self.saved: dict[tuple[str, str, str], Handoff] = {}

    def get(self, resident_id: str, shift_id: str, pattern: str) -> Handoff | None:
        return self.saved.get((resident_id, shift_id, pattern))

    def save(self, handoff: Handoff) -> None:
        self.saved[(handoff.resident_id, handoff.shift_id, handoff.pattern)] = handoff

    def list_for_shift(self, shift_id: str, pattern: str) -> list[Handoff]:
        return [h for (_, s, p), h in self.saved.items() if s == shift_id and p == pattern]


class InMemorySettingsStore:
    def __init__(self, pattern: ShiftPattern | None = None):
        self.pattern = pattern

    def get_shift_pattern(self) -> ShiftPattern | None:
        return self.pattern

    def save_shift_pattern(self, pattern: ShiftPattern) -> None:
        self.pattern = pattern


class FixedClock:
    def __init__(self, now: datetime = datetime(2026, 12, 3, 15, 0)):
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakeHandoffWriter:
    """Deterministic writer: words each detected change and cites its evidence.

    `extra` lets a test inject claims (e.g. a hallucinated citation) into every draft.
    """

    model_name = "fake-writer"

    def __init__(self, extra: tuple[Claim, ...] = (), skip_changes: bool = False):
        self.calls = 0
        self._extra = extra
        self._skip_changes = skip_changes

    def write(self, pack: EvidencePack) -> HandoffDraft:
        self.calls += 1
        changes = (
            ()
            if self._skip_changes
            else tuple(
                ChangeClaim(c.summary, c.evidence, severity=c.severity) for c in pack.changes
            )
        )
        vitals = tuple(
            Claim(line.text, (line.source_id,))
            for line in pack.lines
            if line.kind is SourceKind.VITAL
        )
        return HandoffDraft(changes=changes, sbar=Sbar(assessment=vitals, situation=self._extra))
