import pytest

from handoff.domain.entities import Incident, Note, ShiftWindow, VitalSign
from handoff.domain.value_objects import SourceId

from .conftest import at


def test_collects_records_and_ids(resident, day_shift) -> None:
    note = Note(SourceId("N88"), "R07", at(14, 30), "RN", "found on floor")
    fall = Incident(SourceId("I12"), "R07", at(14, 20), "fall", "unwitnessed fall")
    vital = VitalSign(SourceId("V231"), "R07", at(14, 35), bp_sys=98, bp_dia=60)
    window = ShiftWindow(resident, day_shift, notes=(note,), vitals=(vital,), incidents=(fall,))

    assert window.source_ids == {SourceId("N88"), SourceId("I12"), SourceId("V231")}
    assert [r.id.value for r in window.chronological()] == ["I12", "N88", "V231"]
    assert window.find(SourceId("V231")) is vital
    assert window.find(SourceId("V999")) is None


def test_rejects_record_outside_the_shift(resident, day_shift) -> None:
    late = Note(SourceId("N1"), "R07", at(15, 0), "RN", "evening note")
    with pytest.raises(ValueError, match="outside shift"):
        ShiftWindow(resident, day_shift, notes=(late,))


def test_rejects_another_residents_record(resident, day_shift) -> None:
    other = Note(SourceId("N1"), "R99", at(9), "RN", "wrong chart")
    with pytest.raises(ValueError, match="belongs to R99"):
        ShiftWindow(resident, day_shift, notes=(other,))
