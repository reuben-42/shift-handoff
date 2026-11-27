from handoff.domain.entities import (
    Baseline,
    Change,
    ChangeClaim,
    Claim,
    EvidenceLine,
    EvidencePack,
    HandoffDraft,
    Sbar,
)
from handoff.domain.services import CitationVerifier, CoverageGuard
from handoff.domain.value_objects import ClaimFlag, Severity, SourceId

I12, N88, V231, FAKE = SourceId("I12"), SourceId("N88"), SourceId("V231"), SourceId("V999")


def pack(resident, shift, *ids: SourceId) -> EvidencePack:
    lines = tuple(EvidenceLine(i, "...") for i in ids)
    return EvidencePack(resident, shift, Baseline("R07"), lines, ())


# --- CitationVerifier ---------------------------------------------------------


def test_keeps_claims_whose_sources_all_exist(resident, day_shift) -> None:
    draft = HandoffDraft(
        changes=(ChangeClaim("Fall", (I12, N88), severity=Severity.HIGH),),
        sbar=Sbar(assessment=(Claim("BP 98/60", (V231,)),)),
    )
    result = CitationVerifier().verify(draft, pack(resident, day_shift, I12, N88, V231))
    assert result.draft == draft
    assert (result.claims_checked, result.dropped, result.flagged) == (2, (), 0)


def test_drops_claims_citing_only_unknown_ids(resident, day_shift) -> None:
    draft = HandoffDraft((), Sbar(situation=(Claim("Invented", (FAKE,)), Claim("Real", (I12,)))))
    result = CitationVerifier().verify(draft, pack(resident, day_shift, I12))
    assert [c.text for c in result.draft.claims()] == ["Real"]
    assert result.dropped[0].text == "Invented"
    assert "V999" in result.dropped[0].reason


def test_drops_claims_with_no_sources(resident, day_shift) -> None:
    draft = HandoffDraft((), Sbar(background=(Claim("Unsourced", ()),)))
    result = CitationVerifier().verify(draft, pack(resident, day_shift, I12))
    assert list(result.draft.claims()) == []
    assert result.dropped[0].reason == "cites no sources"


def test_strips_unknown_ids_and_flags_partly_cited_claims(resident, day_shift) -> None:
    draft = HandoffDraft(
        changes=(ChangeClaim("Fall", (I12, FAKE), severity=Severity.HIGH),), sbar=Sbar()
    )
    result = CitationVerifier().verify(draft, pack(resident, day_shift, I12))
    [claim] = result.draft.changes
    assert claim.sources == (I12,)
    assert claim.flag is ClaimFlag.PARTIALLY_SUPPORTED
    assert claim.severity is Severity.HIGH  # ChangeClaim keeps its type
    assert result.flagged == 1 and result.dropped == ()


def test_checks_every_sbar_section(resident, day_shift) -> None:
    bad = (Claim("x", (FAKE,)),)
    draft = HandoffDraft((), Sbar(bad, bad, bad, bad))
    result = CitationVerifier().verify(draft, pack(resident, day_shift))
    assert result.claims_checked == 4 and len(result.dropped) == 4


# --- CoverageGuard ------------------------------------------------------------

FALL = Change("IncidentRule", "Fall at 14:20: unwitnessed", Severity.HIGH, (I12,))
HELD = Change("MissedDoseRule", "amlodipine held", Severity.MEDIUM, (SourceId("M1"),))


def test_covered_high_change_adds_nothing() -> None:
    draft = HandoffDraft((), Sbar(situation=(Claim("Found on floor", (I12, N88)),)))
    result = CoverageGuard().ensure(draft, [FALL])
    assert result.draft == draft and result.added == ()


def test_uncovered_high_change_gets_a_templated_claim() -> None:
    draft = HandoffDraft((), Sbar(assessment=(Claim("BP fine", (V231,)),)))
    result = CoverageGuard().ensure(draft, [FALL])
    [added] = result.added
    assert added == ChangeClaim("Fall at 14:20: unwitnessed", (I12,), severity=Severity.HIGH)
    assert result.draft.changes[-1] == added
    assert result.draft.sbar == draft.sbar


def test_medium_changes_are_not_forced_by_default() -> None:
    draft = HandoffDraft((), Sbar())
    assert CoverageGuard().ensure(draft, [HELD]).added == ()


def test_threshold_is_configurable() -> None:
    result = CoverageGuard(min_severity=Severity.MEDIUM).ensure(HandoffDraft((), Sbar()), [HELD])
    assert [c.text for c in result.added] == ["amlodipine held"]
