"""Claims, drafts and the final handoff (see the output schema in docs/PLAN.md)."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from handoff.domain.value_objects import ClaimFlag, Priority, Severity, SourceId


class SbarSection(StrEnum):
    SITUATION = "situation"
    BACKGROUND = "background"
    ASSESSMENT = "assessment"
    RECOMMENDATION = "recommendation"


@dataclass(frozen=True)
class Claim:
    """One sentence and the records it rests on. Drafts may have none; handoffs may not."""

    text: str
    sources: tuple[SourceId, ...]
    flag: ClaimFlag | None = None

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("A claim needs text")


@dataclass(frozen=True)
class ChangeClaim(Claim):
    """A "what changed" line: a claim with a severity."""

    severity: Severity = Severity.LOW


@dataclass(frozen=True)
class Sbar:
    situation: tuple[Claim, ...] = ()
    background: tuple[Claim, ...] = ()
    assessment: tuple[Claim, ...] = ()
    recommendation: tuple[Claim, ...] = ()

    def section(self, name: SbarSection) -> tuple[Claim, ...]:
        return getattr(self, name.value)

    def claims(self) -> Iterator[Claim]:
        for name in SbarSection:
            yield from self.section(name)


@dataclass(frozen=True)
class HandoffDraft:
    """What a HandoffWriter returns, before verification."""

    changes: tuple[ChangeClaim, ...]
    sbar: Sbar

    def claims(self) -> Iterator[Claim]:
        yield from self.changes
        yield from self.sbar.claims()


@dataclass(frozen=True)
class VerificationSummary:
    claims_checked: int = 0
    dropped: int = 0
    flagged: int = 0


@dataclass(frozen=True)
class Handoff:
    """A verified handoff for one resident, one shift, under one shift pattern."""

    resident_id: str
    shift_id: str
    pattern: str
    priority: Priority
    changes: tuple[ChangeClaim, ...]
    sbar: Sbar
    verification: VerificationSummary
    model: str
    created_at: datetime
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None

    def __post_init__(self) -> None:
        # Safety rule: no claim without a source reaches the UI.
        for claim in self.claims():
            if not claim.sources:
                raise ValueError(f"Unsourced claim cannot be in a handoff: {claim.text!r}")
        if (self.acknowledged_by is None) != (self.acknowledged_at is None):
            raise ValueError("acknowledged_by and acknowledged_at go together")

    @property
    def id(self) -> str:
        return f"{self.resident_id}:{self.shift_id}:{self.pattern}"

    @property
    def acknowledged(self) -> bool:
        return self.acknowledged_by is not None

    def claims(self) -> Iterator[Claim]:
        yield from self.changes
        yield from self.sbar.claims()
