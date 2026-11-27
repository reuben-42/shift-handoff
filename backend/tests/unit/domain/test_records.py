import pytest

from handoff.domain.entities import Incident, MedAdministration, Note, Order, VitalSign
from handoff.domain.value_objects import MedStatus, SourceId

from .conftest import at


def test_each_record_requires_its_own_prefix() -> None:
    Note(SourceId("N1"), "R07", at(9), "RN", "pt resting")
    with pytest.raises(ValueError, match="must start with N"):
        Note(SourceId("V1"), "R07", at(9), "RN", "pt resting")
    with pytest.raises(ValueError, match="must start with V"):
        VitalSign(SourceId("N1"), "R07", at(9))
    with pytest.raises(ValueError, match="must start with M"):
        MedAdministration(SourceId("O1"), "R07", at(9), "amlodipine", "5 mg", MedStatus.GIVEN)
    with pytest.raises(ValueError, match="must start with O"):
        Order(SourceId("I1"), "R07", at(9), "med", "start amlodipine")
    with pytest.raises(ValueError, match="must start with I"):
        Incident(SourceId("M1"), "R07", at(9), "fall", "found on floor")


@pytest.mark.parametrize("pain", [-1, 11])
def test_pain_score_is_0_to_10(pain: int) -> None:
    with pytest.raises(ValueError):
        VitalSign(SourceId("V1"), "R07", at(9), pain_0_10=pain)


def test_spo2_is_a_percentage() -> None:
    with pytest.raises(ValueError):
        VitalSign(SourceId("V1"), "R07", at(9), spo2=101)


def test_records_are_immutable() -> None:
    note = Note(SourceId("N1"), "R07", at(9), "RN", "pt resting")
    with pytest.raises(AttributeError):
        note.text = "edited"  # type: ignore[misc]
