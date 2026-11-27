from dataclasses import dataclass
from datetime import date, datetime

from handoff.domain.value_objects import ShiftKind


@dataclass(frozen=True)
class Shift:
    """One concrete shift: a pattern's shift kind on a date.

    A shift belongs to the date it starts on, so a night shift starting
    2026-12-03 23:00 is "2026-12-03-night" even though it ends on the 4th.
    """

    date: date
    kind: ShiftKind
    start: datetime
    end: datetime
    pattern: str

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("Shift must end after it starts")

    @property
    def id(self) -> str:
        return f"{self.date.isoformat()}-{self.kind}"

    def contains(self, moment: datetime) -> bool:
        """Half-open window: start is inside, end belongs to the next shift."""
        return self.start <= moment < self.end
