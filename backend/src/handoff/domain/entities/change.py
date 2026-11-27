from dataclasses import dataclass

from handoff.domain.value_objects import Severity, SourceId


@dataclass(frozen=True)
class Change:
    """Something a ChangeRule decided is worth handing off. No AI involved."""

    rule: str
    summary: str
    severity: Severity
    evidence: tuple[SourceId, ...]

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("A change must cite the records that triggered it")
