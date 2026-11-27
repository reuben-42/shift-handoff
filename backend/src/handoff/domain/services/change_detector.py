from collections.abc import Sequence

from handoff.domain.entities import Baseline, Change, ShiftWindow
from handoff.domain.rules import ChangeRule


class ChangeDetector:
    """Runs every registered rule. Never edited to add a rule: register a new class instead."""

    def __init__(self, rules: Sequence[ChangeRule]):
        self._rules = tuple(rules)

    def detect(self, window: ShiftWindow, baseline: Baseline) -> list[Change]:
        changes = [change for rule in self._rules for change in rule.evaluate(window, baseline)]
        # Most severe first; stable, so rules keep their own order within a severity.
        return sorted(changes, key=lambda c: -c.severity.rank)
