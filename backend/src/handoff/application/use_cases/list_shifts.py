from handoff.application.dto import ShiftDTO
from handoff.application.ports import ShiftReader
from handoff.application.services import ActivePattern
from handoff.domain.services import ShiftCalendar


class ListShifts:
    """Shifts for the picker: every shift of the active pattern on dates that have data."""

    def __init__(self, shifts: ShiftReader, pattern: ActivePattern, calendar: ShiftCalendar):
        self._shifts = shifts
        self._pattern = pattern
        self._calendar = calendar

    def execute(self) -> list[ShiftDTO]:
        dates = self._shifts.date_range()
        if dates is None:
            return []
        first, last = dates
        shifts = self._calendar.shifts_between(self._pattern.get(), first, last)
        return [ShiftDTO.from_entity(s) for s in shifts]
