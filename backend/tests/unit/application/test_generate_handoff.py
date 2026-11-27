import pytest

from handoff.application.dto import GenerateHandoffCommand
from handoff.application.errors import InvalidShift, ResidentNotFound
from handoff.domain.entities import Claim
from handoff.domain.value_objects import TWO_TWELVE, SourceId
from tests.fakes import FakeHandoffWriter

from .conftest import DAY_SHIFT, World


def test_generates_a_cited_handoff_with_changes_first(world: World) -> None:
    dto = world.generate().execute(GenerateHandoffCommand("R01", DAY_SHIFT))

    assert dto.id == "R01:2026-12-03-day:3x8"
    assert dto.priority == "high"
    assert [(c.text, c.sources, c.severity) for c in dto.changes] == [
        ("Fall at 14:20: found on floor beside bed", ("I12",), "high")
    ]
    assert [c.sources for c in dto.sbar.assessment] == [("V231",)]
    assert dto.model == "fake-writer"
    assert world.store.get("R01", DAY_SHIFT, "3x8") is not None


def test_quiet_shift_has_no_changes(world: World) -> None:
    dto = world.generate().execute(GenerateHandoffCommand("R02", DAY_SHIFT))
    assert dto.priority == "none"
    assert dto.changes == ()


def test_only_records_inside_the_shift_are_used(world: World) -> None:
    # R03's 17:00 refusal is in the evening shift, so the day shift only sees the held dose.
    dto = world.generate().execute(GenerateHandoffCommand("R03", DAY_SHIFT))
    assert [c.sources for c in dto.changes] == [("M5",)]
    assert dto.priority == "medium"


def test_returns_the_cached_handoff_unless_forced(world: World) -> None:
    use_case = world.generate()
    first = use_case.execute(GenerateHandoffCommand("R01", DAY_SHIFT))
    second = use_case.execute(GenerateHandoffCommand("R01", DAY_SHIFT))
    assert second == first
    assert world.writer.calls == 1

    use_case.execute(GenerateHandoffCommand("R01", DAY_SHIFT, force=True))
    assert world.writer.calls == 2


def test_verifier_runs_before_saving() -> None:
    hallucinated = Claim("Daughter visited", (SourceId("N999"),))
    world = World(FakeHandoffWriter(extra=(hallucinated,), skip_changes=True))

    dto = world.generate().execute(GenerateHandoffCommand("R01", DAY_SHIFT))

    # The invented claim is dropped; the fall the writer "forgot" is added back.
    assert all(c.text != "Daughter visited" for c in dto.sbar.situation)
    assert dto.verification.dropped == 1
    assert [c.sources for c in dto.changes] == [("I12",)]
    saved = world.store.get("R01", DAY_SHIFT, "3x8")
    assert saved is not None and saved.verification.dropped == 1


def test_switching_pattern_changes_window_and_cache_key(world: World) -> None:
    world.settings.save_shift_pattern(TWO_TWELVE)
    dto = world.generate().execute(GenerateHandoffCommand("R03", DAY_SHIFT))
    # Day shift is now 07:00-19:00, so it holds both the held and the refused dose.
    assert [c.sources for c in dto.changes] == [("M5", "M6")]
    assert dto.priority == "high"
    assert dto.pattern == "2x12"
    assert world.store.get("R03", DAY_SHIFT, "3x8") is None


def test_unknown_resident(world: World) -> None:
    with pytest.raises(ResidentNotFound):
        world.generate().execute(GenerateHandoffCommand("R99", DAY_SHIFT))


@pytest.mark.parametrize("shift_id", ["2026-12-03-brunch", "nonsense"])
def test_invalid_shift(world: World, shift_id: str) -> None:
    with pytest.raises(InvalidShift):
        world.generate().execute(GenerateHandoffCommand("R01", shift_id))


def test_evening_does_not_exist_under_two_twelve(world: World) -> None:
    world.settings.save_shift_pattern(TWO_TWELVE)
    with pytest.raises(InvalidShift):
        world.generate().execute(GenerateHandoffCommand("R01", "2026-12-03-evening"))
