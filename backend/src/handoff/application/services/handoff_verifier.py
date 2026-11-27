"""Pipeline step 5 (Verify). Combines the domain checks; the LLM judge joins in step 13.

Lives in Application (not Domain) because the judge will be a port.
"""

import logging
from collections.abc import Sequence

from handoff.application.ports import Clock
from handoff.domain.entities import Change, EvidencePack, Handoff, HandoffDraft, VerificationSummary
from handoff.domain.services import CitationVerifier, CoverageGuard, PriorityCalculator

log = logging.getLogger(__name__)


class HandoffVerifier:
    def __init__(
        self,
        citations: CitationVerifier,
        coverage: CoverageGuard,
        priority: PriorityCalculator,
        clock: Clock,
    ):
        self._citations = citations
        self._coverage = coverage
        self._priority = priority
        self._clock = clock

    def verify(
        self, draft: HandoffDraft, pack: EvidencePack, changes: Sequence[Change], model: str
    ) -> Handoff:
        cited = self._citations.verify(draft, pack)
        for dropped in cited.dropped:
            log.info(
                "Dropped claim for %s: %r (%s)", pack.resident.id, dropped.text, dropped.reason
            )

        covered = self._coverage.ensure(cited.draft, changes)
        # "What changed" first, most severe first (stable within a severity).
        ordered = tuple(sorted(covered.draft.changes, key=lambda c: -c.severity.rank))

        return Handoff(
            resident_id=pack.resident.id,
            shift_id=pack.shift.id,
            pattern=pack.shift.pattern,
            priority=self._priority.calculate(changes),
            changes=ordered,
            sbar=covered.draft.sbar,
            verification=VerificationSummary(
                claims_checked=cited.claims_checked,
                dropped=len(cited.dropped),
                flagged=cited.flagged,
            ),
            model=model,
            created_at=self._clock.now(),
        )
