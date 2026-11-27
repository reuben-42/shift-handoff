from enum import StrEnum


class Priority(StrEnum):
    """A resident's place on the unit board. NONE means "No changes this shift"."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

    @property
    def rank(self) -> int:
        return {"high": 3, "medium": 2, "low": 1, "none": 0}[self.value]
