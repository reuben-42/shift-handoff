from handoff.application.dto import BoardCardDTO, BoardDTO, ShiftDTO
from handoff.application.ports import HandoffStore, ResidentReader
from handoff.application.services import ActivePattern, EvidenceGatherer
from handoff.application.use_cases._shifts import resolve_shift
from handoff.domain.entities import Resident, Shift
from handoff.domain.services import ChangeDetector, PriorityCalculator, ShiftCalendar
from handoff.domain.value_objects import Priority


class GetUnitBoard:
    """Resident cards for one shift, most urgent first.

    A card uses the saved handoff when there is one; otherwise it runs the rules
    alone (cheap, no model call) so the board is complete before any handoff exists.
    """

    def __init__(
        self,
        residents: ResidentReader,
        gatherer: EvidenceGatherer,
        detector: ChangeDetector,
        priority: PriorityCalculator,
        store: HandoffStore,
        pattern: ActivePattern,
        calendar: ShiftCalendar,
    ):
        self._residents = residents
        self._gatherer = gatherer
        self._detector = detector
        self._priority = priority
        self._store = store
        self._pattern = pattern
        self._calendar = calendar

    def execute(self, shift_id: str) -> BoardDTO:
        pattern = self._pattern.get()
        shift = resolve_shift(self._calendar, pattern, shift_id)
        cards = [self._card(r, shift) for r in self._residents.list_residents()]
        cards.sort(key=lambda c: (-Priority(c.priority).rank, c.room))
        return BoardDTO(shift=ShiftDTO.from_entity(shift), cards=tuple(cards))

    def _card(self, resident: Resident, shift: Shift) -> BoardCardDTO:
        handoff = self._store.get(resident.id, shift.id, shift.pattern)
        if handoff is not None:
            priority = handoff.priority
            top = handoff.changes[0].text if handoff.changes else None
            count = len(handoff.changes)
        else:
            changes = self._detector.detect(*self._gatherer.gather(resident, shift))
            priority = self._priority.calculate(changes)
            top = changes[0].summary if changes else None
            count = len(changes)
        return BoardCardDTO(
            resident_id=resident.id,
            room=resident.room,
            name=resident.name,
            age=resident.age,
            priority=priority.value,
            top_change=top,
            change_count=count,
            acknowledged=bool(handoff and handoff.acknowledged),
            handoff_ready=handoff is not None,
        )
