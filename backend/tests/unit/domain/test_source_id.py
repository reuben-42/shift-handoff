import pytest

from handoff.domain.value_objects import SourceId, SourceKind


@pytest.mark.parametrize(
    ("value", "kind"),
    [
        ("N88", SourceKind.NOTE),
        ("V231", SourceKind.VITAL),
        ("M7", SourceKind.MED),
        ("O31", SourceKind.ORDER),
        ("I12", SourceKind.INCIDENT),
    ],
)
def test_accepts_known_prefixes(value: str, kind: SourceKind) -> None:
    source = SourceId(value)
    assert source.kind is kind
    assert str(source) == value


@pytest.mark.parametrize("value", ["X12", "n88", "V", "88", "V12a", " V12", "", "VV12"])
def test_rejects_everything_else(value: str) -> None:
    with pytest.raises(ValueError):
        SourceId(value)
    assert not SourceId.is_valid(value)


def test_is_a_value() -> None:
    assert SourceId("V1") == SourceId("V1")
    assert len({SourceId("V1"), SourceId("V1")}) == 1
