"""Turns a ShiftPattern into concrete shifts on real dates."""

from datetime import date, datetime, timedelta

from handoff.domain.entities.shift import Shift
from handoff.domain.value_objects import ShiftKind, ShiftPattern


class ShiftCalendar:
    def shift(self, pattern: ShiftPattern, on: date, kind: ShiftKind) -> Shift:
        definition = pattern.definition(kind)
        start = datetime.combine(on, definition.start)
        return Shift(
            date=on,
            kind=kind,
            start=start,
            end=start + timedelta(hours=definition.hours),
            pattern=pattern.name,
        )

    def shifts_on(self, pattern: ShiftPattern, on: date) -> list[Shift]:
        return [self.shift(pattern, on, kind) for kind in pattern.kinds]

    def shifts_between(self, pattern: ShiftPattern, first: date, last: date) -> list[Shift]:
        """Every shift starting on any date from `first` to `last`, inclusive, in order."""
        if last < first:
            raise ValueError("last date is before first date")
        days = (last - first).days + 1
        shifts = [s for d in range(days) for s in self.shifts_on(pattern, first + timedelta(d))]
        return sorted(shifts, key=lambda s: s.start)

    def shift_containing(self, pattern: ShiftPattern, moment: datetime) -> Shift:
        # A moment can only fall in a shift that started today or yesterday.
        for on in (moment.date(), moment.date() - timedelta(days=1)):
            for shift in self.shifts_on(pattern, on):
                if shift.contains(moment):
                    return shift
        raise AssertionError("A valid 24-hour pattern always contains every moment")

    def parse(self, pattern: ShiftPattern, shift_id: str) -> Shift:
        """'2026-12-03-night' -> the Shift under this pattern. Raises ValueError if invalid."""
        try:
            date_part, kind_part = shift_id.rsplit("-", 1)
            on = date.fromisoformat(date_part)
            kind = ShiftKind(kind_part)
        except ValueError as exc:
            raise ValueError(f"Invalid shift id {shift_id!r}") from exc
        if kind not in pattern.kinds:
            raise ValueError(f"Pattern {pattern.name!r} has no {kind} shift")
        return self.shift(pattern, on, kind)
