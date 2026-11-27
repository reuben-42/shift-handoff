from datetime import date, datetime

import pytest

from handoff.domain.services import ShiftCalendar
from handoff.domain.value_objects import THREE_EIGHT, TWO_TWELVE, ShiftKind

calendar = ShiftCalendar()
DEC3 = date(2026, 12, 3)


def test_day_shift_window() -> None:
    shift = calendar.shift(THREE_EIGHT, DEC3, ShiftKind.DAY)
    assert shift.id == "2026-12-03-day"
    assert shift.start == datetime(2026, 12, 3, 7)
    assert shift.end == datetime(2026, 12, 3, 15)


def test_night_shift_crosses_midnight_and_keeps_its_start_date() -> None:
    shift = calendar.shift(THREE_EIGHT, DEC3, ShiftKind.NIGHT)
    assert shift.id == "2026-12-03-night"
    assert shift.start == datetime(2026, 12, 3, 23)
    assert shift.end == datetime(2026, 12, 4, 7)


def test_window_is_half_open() -> None:
    day = calendar.shift(THREE_EIGHT, DEC3, ShiftKind.DAY)
    assert day.contains(datetime(2026, 12, 3, 7))
    assert day.contains(datetime(2026, 12, 3, 14, 59))
    assert not day.contains(datetime(2026, 12, 3, 15))


def test_two_twelve_windows() -> None:
    day, night = calendar.shifts_on(TWO_TWELVE, DEC3)
    assert (day.start.hour, day.end.hour) == (7, 19)
    assert (night.start, night.end) == (datetime(2026, 12, 3, 19), datetime(2026, 12, 4, 7))


@pytest.mark.parametrize(
    ("moment", "pattern", "expected"),
    [
        (datetime(2026, 12, 3, 14, 20), THREE_EIGHT, "2026-12-03-day"),
        (datetime(2026, 12, 3, 15, 0), THREE_EIGHT, "2026-12-03-evening"),
        (datetime(2026, 12, 3, 23, 30), THREE_EIGHT, "2026-12-03-night"),
        (datetime(2026, 12, 4, 2, 0), THREE_EIGHT, "2026-12-03-night"),
        (datetime(2026, 12, 4, 7, 0), THREE_EIGHT, "2026-12-04-day"),
        (datetime(2026, 12, 3, 17, 0), TWO_TWELVE, "2026-12-03-day"),
        (datetime(2026, 12, 4, 6, 59), TWO_TWELVE, "2026-12-03-night"),
    ],
)
def test_shift_containing(moment: datetime, pattern, expected: str) -> None:
    assert calendar.shift_containing(pattern, moment).id == expected


def test_shifts_between_lists_every_shift_in_order() -> None:
    shifts = calendar.shifts_between(THREE_EIGHT, DEC3, date(2026, 12, 5))
    assert len(shifts) == 9  # 3 days x 3 shifts, as in the plan
    assert shifts[0].id == "2026-12-03-day"
    assert shifts[-1].id == "2026-12-05-night"
    assert all(a.end == b.start for a, b in zip(shifts, shifts[1:], strict=False))


def test_shifts_between_rejects_reversed_range() -> None:
    with pytest.raises(ValueError):
        calendar.shifts_between(THREE_EIGHT, DEC3, date(2026, 12, 2))


def test_parse_round_trips() -> None:
    shift = calendar.parse(THREE_EIGHT, "2026-12-03-evening")
    assert shift == calendar.shift(THREE_EIGHT, DEC3, ShiftKind.EVENING)


@pytest.mark.parametrize("bad", ["2026-12-03-brunch", "yesterday-day", "2026-13-01-day", "day"])
def test_parse_rejects_garbage(bad: str) -> None:
    with pytest.raises(ValueError):
        calendar.parse(THREE_EIGHT, bad)


def test_parse_rejects_kind_missing_from_pattern() -> None:
    with pytest.raises(ValueError, match="no evening"):
        calendar.parse(TWO_TWELVE, "2026-12-03-evening")
