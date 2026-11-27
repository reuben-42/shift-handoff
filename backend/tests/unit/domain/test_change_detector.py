from handoff.domain.entities import Baseline, Change, ShiftWindow
from handoff.domain.services import ChangeDetector, PriorityCalculator
from handoff.domain.value_objects import Priority, Severity, SourceId


class StubRule:
    def __init__(self, name: str, *severities: Severity):
        self.name = name
        self._severities = severities

    def evaluate(self, window, baseline) -> list[Change]:
        return [
            Change(self.name, f"{self.name}-{i}", s, (SourceId(f"N{i}"),))
            for i, s in enumerate(self._severities)
        ]


def test_runs_every_rule_and_sorts_most_severe_first(resident, day_shift) -> None:
    detector = ChangeDetector(
        [StubRule("a", Severity.LOW, Severity.HIGH), StubRule("b", Severity.MEDIUM, Severity.HIGH)]
    )
    changes = detector.detect(ShiftWindow(resident, day_shift), Baseline("R07"))
    assert [(c.summary, c.severity) for c in changes] == [
        ("a-1", Severity.HIGH),
        ("b-1", Severity.HIGH),
        ("b-0", Severity.MEDIUM),
        ("a-0", Severity.LOW),
    ]


def test_no_rules_no_changes(resident, day_shift) -> None:
    assert ChangeDetector([]).detect(ShiftWindow(resident, day_shift), Baseline("R07")) == []


def test_priority_is_the_worst_change() -> None:
    calc = PriorityCalculator()
    medium = Change("r", "m", Severity.MEDIUM, (SourceId("N1"),))
    high = Change("r", "h", Severity.HIGH, (SourceId("N2"),))
    low = Change("r", "l", Severity.LOW, (SourceId("N3"),))
    assert calc.calculate([]) is Priority.NONE
    assert calc.calculate([low]) is Priority.LOW
    assert calc.calculate([low, medium]) is Priority.MEDIUM
    assert calc.calculate([medium, high, low]) is Priority.HIGH
