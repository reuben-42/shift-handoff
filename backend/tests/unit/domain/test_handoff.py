from datetime import datetime

import pytest

from handoff.domain.entities import (
    Change,
    ChangeClaim,
    Claim,
    Handoff,
    HandoffDraft,
    Sbar,
    SbarSection,
    VerificationSummary,
)
from handoff.domain.value_objects import Priority, Severity, SourceId

V231, I12 = SourceId("V231"), SourceId("I12")


def make_handoff(**overrides) -> Handoff:
    fields = dict(
        resident_id="R07",
        shift_id="2026-12-03-day",
        pattern="3x8",
        priority=Priority.HIGH,
        changes=(ChangeClaim("Unwitnessed fall at 14:20", (I12,), severity=Severity.HIGH),),
        sbar=Sbar(assessment=(Claim("BP 98/60", (V231,)),)),
        verification=VerificationSummary(claims_checked=2),
        model="fake",
        created_at=datetime(2026, 12, 3, 15),
    )
    return Handoff(**{**fields, **overrides})


def test_handoff_id_includes_the_pattern() -> None:
    assert make_handoff().id == "R07:2026-12-03-day:3x8"


def test_handoff_rejects_unsourced_claims() -> None:
    with pytest.raises(ValueError, match="Unsourced"):
        make_handoff(sbar=Sbar(situation=(Claim("Resident seems fine", ()),)))


def test_draft_may_hold_unsourced_claims_until_verified() -> None:
    draft = HandoffDraft(changes=(), sbar=Sbar(situation=(Claim("Seems fine", ()),)))
    assert [c.text for c in draft.claims()] == ["Seems fine"]


def test_claims_iterate_changes_then_sbar_in_order() -> None:
    sbar = Sbar(
        situation=(Claim("S", (I12,)),),
        recommendation=(Claim("R", (V231,)),),
    )
    handoff = make_handoff(sbar=sbar)
    assert [c.text for c in handoff.claims()] == ["Unwitnessed fall at 14:20", "S", "R"]
    assert handoff.sbar.section(SbarSection.RECOMMENDATION)[0].text == "R"


def test_acknowledgement_fields_go_together() -> None:
    assert not make_handoff().acknowledged
    assert make_handoff(
        acknowledged_by="Nurse Kim", acknowledged_at=datetime(2026, 12, 3, 15, 5)
    ).acknowledged
    with pytest.raises(ValueError):
        make_handoff(acknowledged_by="Nurse Kim")


def test_claim_needs_text() -> None:
    with pytest.raises(ValueError):
        Claim("  ", (V231,))


def test_change_must_cite_evidence() -> None:
    with pytest.raises(ValueError):
        Change("IncidentRule", "Fall", Severity.HIGH, ())


def test_severity_and_priority_rank() -> None:
    assert Severity.HIGH.rank > Severity.MEDIUM.rank > Severity.LOW.rank
    assert Priority.HIGH.rank > Priority.LOW.rank > Priority.NONE.rank
