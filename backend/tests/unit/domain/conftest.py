from datetime import date, datetime

import pytest

from handoff.domain.entities import Resident, Shift
from handoff.domain.services import ShiftCalendar
from handoff.domain.value_objects import THREE_EIGHT, ShiftKind


@pytest.fixture
def resident() -> Resident:
    return Resident(id="R07", name="Margaret Ellis", room="2B-07", age=84)


@pytest.fixture
def day_shift() -> Shift:
    return ShiftCalendar().shift(THREE_EIGHT, date(2026, 12, 3), ShiftKind.DAY)


def at(hour: int, minute: int = 0, day: int = 3) -> datetime:
    return datetime(2026, 12, day, hour, minute)
