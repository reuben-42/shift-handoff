from typing import Protocol

from handoff.domain.entities import EvidencePack, HandoffDraft


class HandoffWriter(Protocol):
    """Turns an evidence pack into a draft. Every implementation passes one contract suite."""

    @property
    def model_name(self) -> str: ...

    def write(self, pack: EvidencePack) -> HandoffDraft: ...
