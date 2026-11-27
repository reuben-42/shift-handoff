from handoff.application.dto import SourceRecordDTO
from handoff.application.errors import SourceNotFound
from handoff.application.ports import ClinicalRecordReader
from handoff.domain.value_objects import SourceId


class GetSourceRecord:
    """One record for the source drawer."""

    def __init__(self, records: ClinicalRecordReader):
        self._records = records

    def execute(self, source_id: str) -> SourceRecordDTO:
        if not SourceId.is_valid(source_id):
            raise SourceNotFound(source_id)
        record = self._records.get_source(SourceId(source_id))
        if record is None:
            raise SourceNotFound(source_id)
        return SourceRecordDTO.from_entity(record)
