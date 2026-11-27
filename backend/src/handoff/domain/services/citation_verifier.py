"""Deterministic check: every cited ID must exist in this resident's evidence pack.

For each claim:
- all cited IDs are in the pack       -> keep as is
- some cited IDs are not in the pack  -> strip the unknown IDs and flag it amber
                                         (part of what it rests on is missing)
- no cited ID is in the pack, or none -> drop it (no claim without a source)
"""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import TypeVar

from handoff.domain.entities import Claim, EvidencePack, HandoffDraft, Sbar
from handoff.domain.value_objects import ClaimFlag

C = TypeVar("C", bound=Claim)


@dataclass(frozen=True)
class DroppedClaim:
    text: str
    reason: str


@dataclass(frozen=True)
class CitationResult:
    draft: HandoffDraft
    claims_checked: int
    dropped: tuple[DroppedClaim, ...]
    flagged: int


class CitationVerifier:
    def verify(self, draft: HandoffDraft, pack: EvidencePack) -> CitationResult:
        known = pack.ids
        dropped: list[DroppedClaim] = []
        flagged = 0

        def check(claims: Iterable[C]) -> tuple[C, ...]:
            nonlocal flagged
            kept: list[C] = []
            for claim in claims:
                valid = tuple(s for s in claim.sources if s in known)
                unknown = [str(s) for s in claim.sources if s not in known]
                if not claim.sources:
                    dropped.append(DroppedClaim(claim.text, "cites no sources"))
                elif not valid:
                    dropped.append(DroppedClaim(claim.text, f"unknown sources {unknown}"))
                elif unknown:
                    flagged += 1
                    kept.append(replace(claim, sources=valid, flag=ClaimFlag.PARTIALLY_SUPPORTED))
                else:
                    kept.append(claim)
            return tuple(kept)

        checked = sum(1 for _ in draft.claims())
        cleaned = HandoffDraft(
            changes=check(draft.changes),
            sbar=Sbar(
                situation=check(draft.sbar.situation),
                background=check(draft.sbar.background),
                assessment=check(draft.sbar.assessment),
                recommendation=check(draft.sbar.recommendation),
            ),
        )
        return CitationResult(cleaned, checked, tuple(dropped), flagged)
