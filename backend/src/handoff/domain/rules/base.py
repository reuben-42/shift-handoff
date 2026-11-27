from typing import Protocol

from handoff.domain.entities import Baseline, Change, ShiftWindow


class ChangeRule(Protocol):
    """One rule, one class (open/closed: add rules, never edit ChangeDetector).

    Thresholds are constructor arguments so tests and config can set them.
    """

    name: str

    def evaluate(self, window: ShiftWindow, baseline: Baseline) -> list[Change]: ...
