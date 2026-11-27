"""Plain dataclass DTOs in and out of use cases. No framework types cross this line."""

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from typing import Any

from handoff.domain.entities import (
    ChangeClaim,
    Claim,
    Handoff,
    Incident,
    MedAdministration,
    Note,
    Order,
    Shift,
    SourceRecord,
    VitalSign,
)
from handoff.domain.value_objects import ShiftPattern

# --- Commands -------------------------------------------------------------------


@dataclass(frozen=True)
class GenerateHandoffCommand:
    resident_id: str
    shift_id: str
    force: bool = False


@dataclass(frozen=True)
class ShiftDefinitionDTO:
    kind: str
    start: str  # "HH:MM", 24-hour
    hours: int


@dataclass(frozen=True)
class SetShiftPatternCommand:
    """Either a preset name ("3x8", "2x12") or custom shift definitions."""

    preset: str | None = None
    shifts: tuple[ShiftDefinitionDTO, ...] | None = None


# --- Results --------------------------------------------------------------------


@dataclass(frozen=True)
class ShiftPatternDTO:
    name: str
    shifts: tuple[ShiftDefinitionDTO, ...]
    presets: tuple[str, ...] = ()

    @classmethod
    def from_entity(cls, pattern: ShiftPattern, presets: tuple[str, ...] = ()) -> "ShiftPatternDTO":
        return cls(
            name=pattern.name,
            shifts=tuple(
                ShiftDefinitionDTO(s.kind.value, f"{s.start:%H:%M}", s.hours)
                for s in pattern.shifts
            ),
            presets=presets,
        )


@dataclass(frozen=True)
class ShiftDTO:
    id: str
    date: str
    kind: str
    start: datetime
    end: datetime
    pattern: str

    @classmethod
    def from_entity(cls, shift: Shift) -> "ShiftDTO":
        return cls(
            shift.id,
            shift.date.isoformat(),
            shift.kind.value,
            shift.start,
            shift.end,
            shift.pattern,
        )


@dataclass(frozen=True)
class ClaimDTO:
    text: str
    sources: tuple[str, ...]
    flag: str | None = None
    severity: str | None = None  # set on "what changed" lines only

    @classmethod
    def from_entity(cls, claim: Claim) -> "ClaimDTO":
        return cls(
            text=claim.text,
            sources=tuple(s.value for s in claim.sources),
            flag=claim.flag.value if claim.flag else None,
            severity=claim.severity.value if isinstance(claim, ChangeClaim) else None,
        )


@dataclass(frozen=True)
class SbarDTO:
    situation: tuple[ClaimDTO, ...]
    background: tuple[ClaimDTO, ...]
    assessment: tuple[ClaimDTO, ...]
    recommendation: tuple[ClaimDTO, ...]


@dataclass(frozen=True)
class VerificationDTO:
    claims_checked: int
    dropped: int
    flagged: int


@dataclass(frozen=True)
class HandoffDTO:
    id: str
    resident_id: str
    shift_id: str
    pattern: str
    priority: str
    changes: tuple[ClaimDTO, ...]
    sbar: SbarDTO
    verification: VerificationDTO
    model: str
    created_at: datetime
    acknowledged_by: str | None
    acknowledged_at: datetime | None

    @classmethod
    def from_entity(cls, h: Handoff) -> "HandoffDTO":
        def claims(items: tuple[Claim, ...]) -> tuple[ClaimDTO, ...]:
            return tuple(ClaimDTO.from_entity(c) for c in items)

        return cls(
            id=h.id,
            resident_id=h.resident_id,
            shift_id=h.shift_id,
            pattern=h.pattern,
            priority=h.priority.value,
            changes=claims(h.changes),
            sbar=SbarDTO(
                claims(h.sbar.situation),
                claims(h.sbar.background),
                claims(h.sbar.assessment),
                claims(h.sbar.recommendation),
            ),
            verification=VerificationDTO(
                h.verification.claims_checked, h.verification.dropped, h.verification.flagged
            ),
            model=h.model,
            created_at=h.created_at,
            acknowledged_by=h.acknowledged_by,
            acknowledged_at=h.acknowledged_at,
        )


@dataclass(frozen=True)
class BoardCardDTO:
    resident_id: str
    room: str
    name: str
    age: int
    priority: str
    top_change: str | None
    change_count: int
    acknowledged: bool
    handoff_ready: bool


@dataclass(frozen=True)
class BoardDTO:
    shift: ShiftDTO
    cards: tuple[BoardCardDTO, ...]


_TEXT_FIELD = {Note: "text", Order: "text", Incident: "text"}


@dataclass(frozen=True)
class SourceRecordDTO:
    id: str
    kind: str
    resident_id: str
    time: datetime
    fields: dict[str, Any]
    text: str | None

    @classmethod
    def from_entity(cls, record: SourceRecord) -> "SourceRecordDTO":
        assert is_dataclass(record)
        skip = {"id", "resident_id", "time"}
        values: dict[str, Any] = {}
        for f in fields(record):
            if f.name in skip:
                continue
            value = getattr(record, f.name)
            values[f.name] = getattr(value, "value", value)  # enums -> plain values
        text_field = _TEXT_FIELD.get(type(record))
        text = values.pop(text_field) if text_field else None
        if isinstance(record, VitalSign | MedAdministration):
            values = {k: v for k, v in values.items() if v is not None}
        return cls(
            id=record.id.value,
            kind=record.id.kind.name.lower(),
            resident_id=record.resident_id,
            time=record.time,
            fields=values,
            text=text,
        )
