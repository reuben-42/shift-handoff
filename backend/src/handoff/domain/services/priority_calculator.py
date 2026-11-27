from collections.abc import Iterable

from handoff.domain.entities import Change
from handoff.domain.value_objects import Priority, Severity

_PRIORITY_FOR = {
    Severity.HIGH: Priority.HIGH,
    Severity.MEDIUM: Priority.MEDIUM,
    Severity.LOW: Priority.LOW,
}


class PriorityCalculator:
    """A resident's board priority is their most severe change; no changes means NONE."""

    def calculate(self, changes: Iterable[Change]) -> Priority:
        worst = max((c.severity for c in changes), key=lambda s: s.rank, default=None)
        return Priority.NONE if worst is None else _PRIORITY_FOR[worst]
