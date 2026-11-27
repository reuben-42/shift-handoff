from handoff.domain.entities import (
    Baseline,
    Change,
    Incident,
    MedAdministration,
    Note,
    Order,
    ShiftWindow,
    VitalSign,
)
from handoff.domain.services import EvidencePackBuilder
from handoff.domain.value_objects import MedStatus, Severity, SourceId

from .conftest import at


def test_one_line_per_record_in_time_order(resident, day_shift) -> None:
    window = ShiftWindow(
        resident,
        day_shift,
        notes=(Note(SourceId("N88"), "R07", at(14, 30), "RN", "pt found on floor, no injury"),),
        vitals=(
            VitalSign(SourceId("V231"), "R07", at(14, 35), bp_sys=98, bp_dia=60, hr=88, spo2=95),
        ),
        meds=(
            MedAdministration(
                SourceId("M5"), "R07", at(8), "amlodipine", "5 mg", MedStatus.REFUSED, "nausea"
            ),
        ),
        orders=(Order(SourceId("O31"), "R07", at(10), "lab", "CBC in AM"),),
        incidents=(Incident(SourceId("I12"), "R07", at(14, 20), "fall", "unwitnessed fall"),),
    )
    change = Change("IncidentRule", "Fall at 14:20", Severity.HIGH, (SourceId("I12"),))
    baseline = Baseline("R07", bp_sys=130)

    pack = EvidencePackBuilder().build(window, baseline, [change])

    assert [line.render() for line in pack.lines] == [
        "[M5] 08:00 amlodipine 5 mg REFUSED (nausea)",
        "[O31] 10:00 New order (lab): CBC in AM",
        "[I12] 14:20 Incident (fall): unwitnessed fall",
        "[N88] 14:30 RN note: pt found on floor, no injury",
        "[V231] 14:35 BP 98/60 HR 88 SpO2 95%",
    ]
    assert pack.ids == window.source_ids
    assert pack.changes == (change,)
    assert pack.baseline is baseline
    assert pack.line(SourceId("V231")).kind.value == "V"


def test_vital_line_shows_only_recorded_fields(resident, day_shift) -> None:
    window = ShiftWindow(
        resident,
        day_shift,
        vitals=(
            VitalSign(SourceId("V1"), "R07", at(9), temp_c=38.25, rr=18, pain_0_10=4, weight_kg=61),
            VitalSign(SourceId("V2"), "R07", at(10)),
        ),
    )
    lines = [line.text for line in EvidencePackBuilder().build(window, Baseline("R07"), []).lines]
    assert lines == ["09:00 T 38.2C RR 18 Pain 4/10 Wt 61.0kg", "10:00 vitals recorded (no values)"]


def test_empty_shift_gives_empty_pack(resident, day_shift) -> None:
    pack = EvidencePackBuilder().build(ShiftWindow(resident, day_shift), Baseline("R07"), [])
    assert pack.lines == () and pack.ids == frozenset()
