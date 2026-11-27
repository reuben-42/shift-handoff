from handoff.application.errors import InvalidShift
from handoff.domain.entities import Shift
from handoff.domain.services import ShiftCalendar
from handoff.domain.value_objects import ShiftPattern


def resolve_shift(calendar: ShiftCalendar, pattern: ShiftPattern, shift_id: str) -> Shift:
    try:
        return calendar.parse(pattern, shift_id)
    except ValueError as exc:
        raise InvalidShift(str(exc)) from exc
