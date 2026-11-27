"""Deterministic check: every high-severity change must reach the nurse.

A change counts as covered if any claim in the draft cites at least one of the
records that triggered it. If not, a templated "what changed" line built from the
rule's own output is appended, so the LLM can never silently leave out a fall.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from handoff.domain.entities import Change, ChangeClaim, HandoffDraft
from handoff.domain.value_objects import Severity


@dataclass(frozen=True)
class CoverageResult:
    draft: HandoffDraft
    added: tuple[ChangeClaim, ...]


class CoverageGuard:
    def __init__(self, min_severity: Severity = Severity.HIGH):
        self._min_rank = min_severity.rank

    def ensure(self, draft: HandoffDraft, changes: Sequence[Change]) -> CoverageResult:
        cited = {source for claim in draft.claims() for source in claim.sources}
        added = tuple(
            ChangeClaim(text=change.summary, sources=change.evidence, severity=change.severity)
            for change in changes
            if change.severity.rank >= self._min_rank and cited.isdisjoint(change.evidence)
        )
        if not added:
            return CoverageResult(draft, ())
        return CoverageResult(HandoffDraft(draft.changes + added, draft.sbar), added)
