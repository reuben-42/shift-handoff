from datetime import time

from handoff.application.dto import SetShiftPatternCommand, ShiftDefinitionDTO, ShiftPatternDTO
from handoff.application.errors import InvalidShiftPattern
from handoff.application.ports import SettingsStore
from handoff.application.services import ActivePattern
from handoff.domain.value_objects import PRESETS, ShiftDefinition, ShiftKind, ShiftPattern

_PRESET_NAMES = tuple(PRESETS)


class GetShiftPattern:
    def __init__(self, pattern: ActivePattern):
        self._pattern = pattern

    def execute(self) -> ShiftPatternDTO:
        return ShiftPatternDTO.from_entity(self._pattern.get(), _PRESET_NAMES)


class SetShiftPattern:
    """Switch the unit's shift pattern from inside the app (preset or custom times)."""

    def __init__(self, settings: SettingsStore):
        self._settings = settings

    def execute(self, cmd: SetShiftPatternCommand) -> ShiftPatternDTO:
        pattern = self._build(cmd)
        self._settings.save_shift_pattern(pattern)
        return ShiftPatternDTO.from_entity(pattern, _PRESET_NAMES)

    def _build(self, cmd: SetShiftPatternCommand) -> ShiftPattern:
        if (cmd.preset is None) == (cmd.shifts is None):
            raise InvalidShiftPattern("Give either a preset or custom shifts, not both")
        if cmd.preset is not None:
            if cmd.preset not in PRESETS:
                raise InvalidShiftPattern(f"Unknown preset {cmd.preset!r}; try {_PRESET_NAMES}")
            return PRESETS[cmd.preset]
        try:
            shifts = tuple(_definition(s) for s in cmd.shifts or ())
            pattern = ShiftPattern("custom", shifts)
        except (ValueError, KeyError) as exc:
            raise InvalidShiftPattern(str(exc)) from exc
        # Custom patterns are named after their times, so the handoff cache never mixes them.
        starts = "-".join(f"{s.start:%H%M}" for s in pattern.shifts)
        return ShiftPattern(f"custom-{len(shifts)}x@{starts}", shifts)


def _definition(dto: ShiftDefinitionDTO) -> ShiftDefinition:
    try:
        return ShiftDefinition(ShiftKind(dto.kind), time.fromisoformat(dto.start), dto.hours)
    except ValueError as exc:
        raise ValueError(f"Invalid shift {dto}: {exc}") from exc
