from dataclasses import dataclass

from handoff.domain.entities.baseline import Baseline
from handoff.domain.entities.change import Change
from handoff.domain.entities.resident import Resident
from handoff.domain.entities.shift import Shift
from handoff.domain.value_objects import SourceId, SourceKind


@dataclass(frozen=True)
class EvidenceLine:
    source_id: SourceId
    text: str  # e.g. "14:35 BP 98/60 HR 88 SpO2 95%"

    @property
    def kind(self) -> SourceKind:
        return self.source_id.kind

    def render(self) -> str:
        return f"[{self.source_id}] {self.text}"


@dataclass(frozen=True)
class EvidencePack:
    """Everything the writer may use: one line per record, plus the detected changes.

    Turning this into prompt text is an adapter job (PromptBuilder).
    """

    resident: Resident
    shift: Shift
    baseline: Baseline
    lines: tuple[EvidenceLine, ...]
    changes: tuple[Change, ...]

    @property
    def ids(self) -> frozenset[SourceId]:
        return frozenset(line.source_id for line in self.lines)

    def line(self, source_id: SourceId) -> EvidenceLine | None:
        return next((line for line in self.lines if line.source_id == source_id), None)
