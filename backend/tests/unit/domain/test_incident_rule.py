from handoff.domain.entities import Baseline, Incident, ShiftWindow
from handoff.domain.rules import IncidentRule
from handoff.domain.value_objects import Severity, SourceId

from .conftest import at


def incident(n: int, kind: str, hour: int = 14):
    return Incident(SourceId(f"I{n}"), "R07", at(hour, 20), kind, "details")


def evaluate(resident, shift, *incidents, rule=None):
    window = ShiftWindow(resident, shift, incidents=incidents)
    return (rule or IncidentRule()).evaluate(window, Baseline("R07"))


def test_no_incidents_no_changes(resident, day_shift) -> None:
    assert evaluate(resident, day_shift) == []


def test_fall_is_high(resident, day_shift) -> None:
    [change] = evaluate(resident, day_shift, incident(12, "fall"))
    assert change.severity is Severity.HIGH
    assert change.evidence == (SourceId("I12"),)
    assert change.summary == "Fall at 14:20: details"


def test_type_match_is_case_insensitive(resident, day_shift) -> None:
    [change] = evaluate(resident, day_shift, incident(1, "Fall"))
    assert change.severity is Severity.HIGH


def test_other_incidents_use_default_severity(resident, day_shift) -> None:
    [skin, behaviour] = evaluate(
        resident, day_shift, incident(1, "skin", hour=9), incident(2, "behaviour", hour=11)
    )
    assert skin.severity is behaviour.severity is Severity.MEDIUM
    assert skin.evidence == (SourceId("I1"),)


def test_one_change_per_incident_in_time_order(resident, day_shift) -> None:
    changes = evaluate(
        resident, day_shift, incident(2, "fall", hour=13), incident(1, "skin", hour=8)
    )
    assert [c.evidence[0].value for c in changes] == ["I1", "I2"]


def test_severities_are_configurable(resident, day_shift) -> None:
    rule = IncidentRule({"skin": Severity.HIGH}, default_severity=Severity.LOW)
    skin, fall = evaluate(
        resident, day_shift, incident(1, "skin", 9), incident(2, "fall"), rule=rule
    )
    assert skin.severity is Severity.HIGH
    assert fall.severity is Severity.LOW
