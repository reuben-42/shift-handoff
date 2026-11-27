from dataclasses import replace

import pytest

from handoff.application.dto import (
    GenerateHandoffCommand,
    SetShiftPatternCommand,
    ShiftDefinitionDTO,
)
from handoff.application.errors import HandoffNotFound, InvalidShiftPattern, SourceNotFound
from handoff.application.use_cases import (
    GetHandoff,
    GetShiftPattern,
    GetSourceRecord,
    ListShifts,
    SetShiftPattern,
)
from handoff.domain.value_objects import TWO_TWELVE

from .conftest import DAY_SHIFT, World, at

# --- GetUnitBoard -----------------------------------------------------------------


def test_board_is_sorted_by_priority_then_room(world: World) -> None:
    board = world.board().execute(DAY_SHIFT)
    assert board.shift.id == DAY_SHIFT
    assert [(c.resident_id, c.priority) for c in board.cards] == [
        ("R01", "high"),
        ("R03", "medium"),
        ("R02", "none"),
    ]
    assert board.cards[0].top_change == "Fall at 14:20: found on floor beside bed"
    assert board.cards[2].top_change is None


def test_board_works_before_any_handoff_exists_without_calling_the_model(world: World) -> None:
    board = world.board().execute(DAY_SHIFT)
    assert world.writer.calls == 0
    assert not any(c.handoff_ready or c.acknowledged for c in board.cards)


def test_board_reads_saved_handoffs_and_acknowledgement(world: World) -> None:
    world.generate().execute(GenerateHandoffCommand("R01", DAY_SHIFT))
    saved = world.store.get("R01", DAY_SHIFT, "3x8")
    world.store.save(replace(saved, acknowledged_by="Nurse Kim", acknowledged_at=at(15, 5)))

    card = world.board().execute(DAY_SHIFT).cards[0]
    assert card.resident_id == "R01"
    assert card.handoff_ready and card.acknowledged


# --- GetHandoff / GetSourceRecord -----------------------------------------------------


def test_get_handoff_reads_cache_only(world: World) -> None:
    get = GetHandoff(world.store, world.pattern, world.calendar)
    with pytest.raises(HandoffNotFound):
        get.execute("R01", DAY_SHIFT)
    world.generate().execute(GenerateHandoffCommand("R01", DAY_SHIFT))
    assert get.execute("R01", DAY_SHIFT).resident_id == "R01"


def test_get_source_record_for_the_drawer(world: World) -> None:
    get = GetSourceRecord(world.records)
    vital = get.execute("V231")
    assert (vital.kind, vital.time, vital.text) == ("vital", at(14, 35), None)
    assert vital.fields == {"bp_sys": 98, "bp_dia": 60, "hr": 88, "spo2": 95}

    note = get.execute("N88")
    assert note.kind == "note" and note.text == "pt found on floor, no visible injury"
    assert note.fields == {"author_role": "RN"}

    med = get.execute("M5")
    assert med.fields == {"med": "metoprolol", "dose": "25 mg", "status": "held", "reason": "HR 52"}


@pytest.mark.parametrize("bad", ["V999", "X1", ""])
def test_get_source_record_not_found(world: World, bad: str) -> None:
    with pytest.raises(SourceNotFound):
        GetSourceRecord(world.records).execute(bad)


# --- ListShifts / shift pattern ---------------------------------------------------------


def test_list_shifts_follows_the_active_pattern(world: World) -> None:
    list_shifts = ListShifts(world.records, world.pattern, world.calendar)
    three = list_shifts.execute()
    assert len(three) == 6  # data on Dec 2-3: 2 days x 3 shifts
    assert three[0].id == "2026-12-02-day"

    world.settings.save_shift_pattern(TWO_TWELVE)
    two = list_shifts.execute()
    assert [s.kind for s in two] == ["day", "night", "day", "night"]


def test_list_shifts_empty_chart(world: World) -> None:
    from tests.fakes import InMemoryClinicalRecordReader

    assert (
        ListShifts(InMemoryClinicalRecordReader([]), world.pattern, world.calendar).execute() == []
    )


def test_get_pattern_defaults_to_three_eight(world: World) -> None:
    dto = GetShiftPattern(world.pattern).execute()
    assert dto.name == "3x8"
    assert [(s.kind, s.start, s.hours) for s in dto.shifts] == [
        ("day", "07:00", 8),
        ("evening", "15:00", 8),
        ("night", "23:00", 8),
    ]
    assert dto.presets == ("3x8", "2x12")


def test_set_preset_pattern(world: World) -> None:
    SetShiftPattern(world.settings).execute(SetShiftPatternCommand(preset="2x12"))
    assert GetShiftPattern(world.pattern).execute().name == "2x12"


def test_set_custom_pattern_gets_a_unique_name(world: World) -> None:
    shifts = (
        ShiftDefinitionDTO("day", "06:00", 8),
        ShiftDefinitionDTO("evening", "14:00", 8),
        ShiftDefinitionDTO("night", "22:00", 8),
    )
    dto = SetShiftPattern(world.settings).execute(SetShiftPatternCommand(shifts=shifts))
    assert dto.name == "custom-3x@0600-1400-2200"
    assert world.pattern.get().name == dto.name


@pytest.mark.parametrize(
    "cmd",
    [
        SetShiftPatternCommand(),
        SetShiftPatternCommand(preset="4x6"),
        SetShiftPatternCommand(preset="3x8", shifts=()),
        SetShiftPatternCommand(shifts=(ShiftDefinitionDTO("day", "07:00", 8),)),
        SetShiftPatternCommand(shifts=(ShiftDefinitionDTO("brunch", "07:00", 24),)),
        SetShiftPatternCommand(shifts=(ShiftDefinitionDTO("day", "7am", 24),)),
    ],
)
def test_invalid_patterns_are_rejected(world: World, cmd: SetShiftPatternCommand) -> None:
    with pytest.raises(InvalidShiftPattern):
        SetShiftPattern(world.settings).execute(cmd)
    assert world.settings.pattern is None
