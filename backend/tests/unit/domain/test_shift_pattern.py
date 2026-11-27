from datetime import time

import pytest

from handoff.domain.value_objects import (
    PRESETS,
    THREE_EIGHT,
    TWO_TWELVE,
    ShiftDefinition,
    ShiftKind,
    ShiftPattern,
)

DAY, EVENING, NIGHT = ShiftKind.DAY, ShiftKind.EVENING, ShiftKind.NIGHT


def test_three_eight_is_the_plans_default() -> None:
    assert [(s.kind, s.start, s.end) for s in THREE_EIGHT.shifts] == [
        (DAY, time(7), time(15)),
        (EVENING, time(15), time(23)),
        (NIGHT, time(23), time(7)),
    ]


def test_two_twelve_has_no_evening() -> None:
    assert TWO_TWELVE.kinds == (DAY, NIGHT)
    assert TWO_TWELVE.definition(NIGHT).end == time(7)
    with pytest.raises(KeyError):
        TWO_TWELVE.definition(EVENING)


def test_presets_by_name() -> None:
    assert PRESETS["3x8"] is THREE_EIGHT
    assert PRESETS["2x12"] is TWO_TWELVE


def test_custom_start_time_is_allowed() -> None:
    pattern = ShiftPattern(
        "6am-3x8",
        (
            ShiftDefinition(DAY, time(6), 8),
            ShiftDefinition(EVENING, time(14), 8),
            ShiftDefinition(NIGHT, time(22), 8),
        ),
    )
    assert pattern.signature != THREE_EIGHT.signature


def test_rejects_gap() -> None:
    with pytest.raises(ValueError, match="must start when"):
        ShiftPattern(
            "gap", (ShiftDefinition(DAY, time(7), 12), ShiftDefinition(NIGHT, time(20), 12))
        )


def test_rejects_overlap() -> None:
    with pytest.raises(ValueError, match="must start when"):
        ShiftPattern(
            "overlap",
            (
                ShiftDefinition(DAY, time(7), 8),
                ShiftDefinition(EVENING, time(14), 8),
                ShiftDefinition(NIGHT, time(23), 8),
            ),
        )


def test_rejects_not_24_hours() -> None:
    with pytest.raises(ValueError, match="24 hours"):
        ShiftPattern(
            "short", (ShiftDefinition(DAY, time(7), 8), ShiftDefinition(NIGHT, time(15), 8))
        )


def test_rejects_duplicate_kind() -> None:
    with pytest.raises(ValueError, match="only once"):
        ShiftPattern("dup", (ShiftDefinition(DAY, time(7), 12), ShiftDefinition(DAY, time(19), 12)))


@pytest.mark.parametrize("hours", [0, 25])
def test_rejects_bad_length(hours: int) -> None:
    with pytest.raises(ValueError):
        ShiftDefinition(DAY, time(7), hours)


def test_rejects_seconds_in_start() -> None:
    with pytest.raises(ValueError):
        ShiftDefinition(DAY, time(7, 0, 30), 8)


def test_single_24_hour_shift_is_valid() -> None:
    pattern = ShiftPattern("1x24", (ShiftDefinition(DAY, time(7), 24),))
    assert pattern.definition(DAY).end == time(7)
