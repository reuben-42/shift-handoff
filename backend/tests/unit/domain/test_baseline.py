from datetime import datetime, timedelta

from handoff.domain.entities import Baseline, VitalSign
from handoff.domain.value_objects import SourceId

SHIFT_START = datetime(2026, 12, 3, 7)


def vital(n: int, days_before: float, **fields) -> VitalSign:
    return VitalSign(SourceId(f"V{n}"), "R07", SHIFT_START - timedelta(days=days_before), **fields)


def test_medians_over_the_last_seven_days() -> None:
    history = [
        vital(1, 1, bp_sys=120, hr=70),
        vital(2, 2, bp_sys=130, hr=80),
        vital(3, 3, bp_sys=140),
        vital(4, 10, bp_sys=200),  # older than 7 days: ignored
    ]
    baseline = Baseline.from_vitals("R07", history, before=SHIFT_START)
    assert baseline.bp_sys == 130
    assert baseline.hr == 75
    assert baseline.spo2 is None


def test_ignores_readings_inside_or_after_the_shift() -> None:
    history = [vital(1, 1, bp_sys=130), vital(2, -0.1, bp_sys=60)]
    assert Baseline.from_vitals("R07", history, before=SHIFT_START).bp_sys == 130


def test_ignores_other_residents() -> None:
    other = VitalSign(SourceId("V9"), "R99", SHIFT_START - timedelta(days=1), bp_sys=200)
    assert Baseline.from_vitals("R07", [other], before=SHIFT_START).bp_sys is None


def test_reference_weight_is_earliest_in_30_days() -> None:
    history = [
        vital(1, 40, weight_kg=80.0),  # outside 30 days
        vital(2, 29, weight_kg=70.0),
        vital(3, 1, weight_kg=66.0),
    ]
    assert Baseline.from_vitals("R07", history, before=SHIFT_START).reference_weight_kg == 70.0


def test_empty_history_gives_empty_baseline() -> None:
    assert Baseline.from_vitals("R07", [], before=SHIFT_START) == Baseline("R07")
