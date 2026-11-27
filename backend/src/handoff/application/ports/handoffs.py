from typing import Protocol

from handoff.domain.entities import Handoff


class HandoffStore(Protocol):
    """Cache of verified handoffs, keyed by (resident, shift, pattern)."""

    def get(self, resident_id: str, shift_id: str, pattern: str) -> Handoff | None: ...

    def save(self, handoff: Handoff) -> None: ...

    def list_for_shift(self, shift_id: str, pattern: str) -> list[Handoff]: ...
