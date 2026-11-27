from handoff.application.ports import SettingsStore
from handoff.domain.value_objects import ShiftPattern


class ActivePattern:
    """The shift pattern in force: the one chosen in the app, else the configured default."""

    def __init__(self, settings: SettingsStore, default: ShiftPattern):
        self._settings = settings
        self._default = default

    def get(self) -> ShiftPattern:
        return self._settings.get_shift_pattern() or self._default
