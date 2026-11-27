from handoff.application.dto import GenerateHandoffCommand, HandoffDTO
from handoff.application.errors import ResidentNotFound
from handoff.application.ports import HandoffStore, HandoffWriter, ResidentReader
from handoff.application.services import ActivePattern, EvidenceGatherer, HandoffVerifier
from handoff.application.use_cases._shifts import resolve_shift
from handoff.domain.services import ChangeDetector, EvidencePackBuilder, ShiftCalendar


class GenerateHandoff:
    """The central use case: gather -> detect -> pack -> write -> verify -> save."""

    def __init__(
        self,
        residents: ResidentReader,
        gatherer: EvidenceGatherer,
        detector: ChangeDetector,
        packer: EvidencePackBuilder,
        writer: HandoffWriter,
        verifier: HandoffVerifier,
        store: HandoffStore,
        pattern: ActivePattern,
        calendar: ShiftCalendar,
    ):
        self._residents = residents
        self._gatherer = gatherer
        self._detector = detector
        self._packer = packer
        self._writer = writer
        self._verifier = verifier
        self._store = store
        self._pattern = pattern
        self._calendar = calendar

    def execute(self, cmd: GenerateHandoffCommand) -> HandoffDTO:
        pattern = self._pattern.get()
        shift = resolve_shift(self._calendar, pattern, cmd.shift_id)
        resident = self._residents.get(cmd.resident_id)
        if resident is None:
            raise ResidentNotFound(cmd.resident_id)

        if not cmd.force and (cached := self._store.get(resident.id, shift.id, pattern.name)):
            return HandoffDTO.from_entity(cached)

        window, baseline = self._gatherer.gather(resident, shift)
        changes = self._detector.detect(window, baseline)
        pack = self._packer.build(window, baseline, changes)
        draft = self._writer.write(pack)
        handoff = self._verifier.verify(draft, pack, changes, model=self._writer.model_name)
        self._store.save(handoff)
        return HandoffDTO.from_entity(handoff)
