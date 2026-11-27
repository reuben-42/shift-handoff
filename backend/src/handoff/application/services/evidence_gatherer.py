from handoff.application.ports import ClinicalRecordReader
from handoff.domain.entities import Baseline, Resident, Shift, ShiftWindow
from handoff.domain.entities.baseline import WEIGHT_LOOKBACK_DAYS


class EvidenceGatherer:
    """Pipeline step 1 (Gather): the shift's records plus the resident's baseline."""

    def __init__(self, records: ClinicalRecordReader):
        self._records = records

    def gather(self, resident: Resident, shift: Shift) -> tuple[ShiftWindow, Baseline]:
        window = self._records.window(resident, shift)
        history = self._records.vitals_before(resident.id, shift.start, WEIGHT_LOOKBACK_DAYS)
        return window, Baseline.from_vitals(resident.id, history, before=shift.start)
