from typing import Protocol

from handoff.domain.value_objects import ShiftPattern


class SettingsStore(Protocol):
    def get_shift_pattern(self) -> ShiftPattern | None:
        """The pattern chosen in the app, or None if never changed."""
        ...

    def save_shift_pattern(self, pattern: ShiftPattern) -> None: ...
