from handoff.application.dto import HandoffDTO
from handoff.application.errors import HandoffNotFound
from handoff.application.ports import HandoffStore
from handoff.application.services import ActivePattern
from handoff.application.use_cases._shifts import resolve_shift
from handoff.domain.services import ShiftCalendar


class GetHandoff:
    """Read a cached handoff only; never calls the model (public demo mode)."""

    def __init__(self, store: HandoffStore, pattern: ActivePattern, calendar: ShiftCalendar):
        self._store = store
        self._pattern = pattern
        self._calendar = calendar

    def execute(self, resident_id: str, shift_id: str) -> HandoffDTO:
        pattern = self._pattern.get()
        shift = resolve_shift(self._calendar, pattern, shift_id)
        handoff = self._store.get(resident_id, shift.id, pattern.name)
        if handoff is None:
            raise HandoffNotFound(resident_id, shift_id)
        return HandoffDTO.from_entity(handoff)
