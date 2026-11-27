from enum import StrEnum


class Severity(StrEnum):
    """How urgent a detected change is. Higher rank = more urgent."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def rank(self) -> int:
        return {"high": 3, "medium": 2, "low": 1}[self.value]
