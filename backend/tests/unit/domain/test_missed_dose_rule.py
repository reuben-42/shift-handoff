import pytest

from handoff.domain.entities import Baseline, MedAdministration, ShiftWindow
from handoff.domain.rules import MissedDoseRule
from handoff.domain.value_objects import MedStatus, Severity, SourceId

from .conftest import at


def med(n: int, status: MedStatus, hour: int = 8, name: str = "amlodipine", reason=None):
    return MedAdministration(SourceId(f"M{n}"), "R07", at(hour), name, "5 mg", status, reason)


def evaluate(resident, shift, *meds, rule=None):
    window = ShiftWindow(resident, shift, meds=meds)
    return (rule or MissedDoseRule()).evaluate(window, Baseline("R07"))


def test_given_doses_are_not_changes(resident, day_shift) -> None:
    assert evaluate(resident, day_shift, med(1, MedStatus.GIVEN)) == []


def test_no_meds_no_changes(resident, day_shift) -> None:
    assert evaluate(resident, day_shift) == []


@pytest.mark.parametrize(
    ("status", "severity"),
    [
        (MedStatus.MISSED, Severity.HIGH),
        (MedStatus.REFUSED, Severity.HIGH),
        (MedStatus.HELD, Severity.MEDIUM),
    ],
)
def test_each_non_given_status_is_a_change(resident, day_shift, status, severity) -> None:
    [change] = evaluate(resident, day_shift, med(1, status, reason="pt asleep"))
    assert change.severity is severity
    assert change.evidence == (SourceId("M1"),)
    assert change.rule == "MissedDoseRule"
    assert change.summary == f"amlodipine 5 mg: {status} at 08:00 (pt asleep)"


def test_groups_by_medication_and_takes_worst_severity(resident, day_shift) -> None:
    changes = evaluate(
        resident,
        day_shift,
        med(2, MedStatus.REFUSED, hour=12),
        med(1, MedStatus.HELD, hour=8),
        med(3, MedStatus.GIVEN, hour=9, name="metformin"),
    )
    [change] = changes
    assert change.evidence == (SourceId("M1"), SourceId("M2"))  # chronological
    assert change.severity is Severity.HIGH
    assert change.summary == "amlodipine 5 mg: held at 08:00, refused at 12:00"


def test_one_change_per_medication(resident, day_shift) -> None:
    changes = evaluate(
        resident, day_shift, med(1, MedStatus.MISSED), med(2, MedStatus.MISSED, name="metformin")
    )
    assert [c.evidence for c in changes] == [(SourceId("M1"),), (SourceId("M2"),)]


def test_severities_are_configurable(resident, day_shift) -> None:
    rule = MissedDoseRule({MedStatus.MISSED: Severity.LOW})
    assert evaluate(resident, day_shift, med(1, MedStatus.HELD), rule=rule) == []
    [change] = evaluate(resident, day_shift, med(1, MedStatus.MISSED), rule=rule)
    assert change.severity is Severity.LOW


def test_given_cannot_be_configured_as_a_change() -> None:
    with pytest.raises(ValueError):
        MissedDoseRule({MedStatus.GIVEN: Severity.LOW})
