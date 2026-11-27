from enum import StrEnum


class MedStatus(StrEnum):
    """eMAR administration outcome."""

    GIVEN = "given"
    REFUSED = "refused"
    HELD = "held"
    MISSED = "missed"
