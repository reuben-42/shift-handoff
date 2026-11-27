"""Shift patterns: how a 24-hour day is split into shifts.

Configurable at runtime (docs/DECISIONS.md section 1). Three 8-hour shifts is the
default; two 12-hour shifts is the built-in alternative; custom start times are allowed.
"""

from dataclasses import dataclass
from datetime import time

from handoff.domain.value_objects.shift_kind import ShiftKind

_MINUTES_PER_DAY = 24 * 60


@dataclass(frozen=True)
class ShiftDefinition:
    kind: ShiftKind
    start: time
    hours: int

    def __post_init__(self) -> None:
        if not 1 <= self.hours <= 24:
            raise ValueError(f"Shift length must be 1-24 hours, got {self.hours}")
        if self.start.second or self.start.microsecond or self.start.tzinfo:
            raise ValueError("Shift start must be a naive time on a whole minute")

    @property
    def start_minute(self) -> int:
        return self.start.hour * 60 + self.start.minute

    @property
    def end(self) -> time:
        end_minute = (self.start_minute + self.hours * 60) % _MINUTES_PER_DAY
        return time(end_minute // 60, end_minute % 60)


@dataclass(frozen=True)
class ShiftPattern:
    """An ordered set of shifts that covers exactly 24 hours with no gaps or overlaps."""

    name: str
    shifts: tuple[ShiftDefinition, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Shift pattern needs a name")
        if not self.shifts:
            raise ValueError("Shift pattern needs at least one shift")
        kinds = [s.kind for s in self.shifts]
        if len(set(kinds)) != len(kinds):
            raise ValueError("Each shift kind may appear only once in a pattern")
        total = sum(s.hours for s in self.shifts)
        if total != 24:
            raise ValueError(f"Shifts must add up to 24 hours, got {total}")
        for current, following in zip(self.shifts, self.shifts[1:] + self.shifts[:1], strict=True):
            expected = (current.start_minute + current.hours * 60) % _MINUTES_PER_DAY
            if following.start_minute != expected:
                raise ValueError(
                    f"{following.kind} must start when {current.kind} ends "
                    f"({current.end:%H:%M}), not at {following.start:%H:%M}"
                )

    @property
    def kinds(self) -> tuple[ShiftKind, ...]:
        return tuple(s.kind for s in self.shifts)

    def definition(self, kind: ShiftKind) -> ShiftDefinition:
        for shift in self.shifts:
            if shift.kind == kind:
                return shift
        raise KeyError(f"Pattern {self.name!r} has no {kind} shift")

    @property
    def signature(self) -> str:
        """Stable key for caching: two patterns with the same times share it."""
        return "|".join(f"{s.kind}@{s.start:%H:%M}+{s.hours}" for s in self.shifts)


THREE_EIGHT = ShiftPattern(
    name="3x8",
    shifts=(
        ShiftDefinition(ShiftKind.DAY, time(7, 0), 8),
        ShiftDefinition(ShiftKind.EVENING, time(15, 0), 8),
        ShiftDefinition(ShiftKind.NIGHT, time(23, 0), 8),
    ),
)

TWO_TWELVE = ShiftPattern(
    name="2x12",
    shifts=(
        ShiftDefinition(ShiftKind.DAY, time(7, 0), 12),
        ShiftDefinition(ShiftKind.NIGHT, time(19, 0), 12),
    ),
)

PRESETS: dict[str, ShiftPattern] = {p.name: p for p in (THREE_EIGHT, TWO_TWELVE)}
