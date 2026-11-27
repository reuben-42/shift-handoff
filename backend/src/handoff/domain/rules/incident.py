"""Any incident (fall, skin issue, behaviour) is a change."""

from collections.abc import Mapping
from types import MappingProxyType

from handoff.domain.entities import Baseline, Change, ShiftWindow
from handoff.domain.value_objects import Severity

DEFAULT_SEVERITY_BY_TYPE: Mapping[str, Severity] = MappingProxyType({"fall": Severity.HIGH})


class IncidentRule:
    """One Change per incident. Falls are high by default; other types use default_severity."""

    name = "IncidentRule"

    def __init__(
        self,
        severity_by_type: Mapping[str, Severity] = DEFAULT_SEVERITY_BY_TYPE,
        default_severity: Severity = Severity.MEDIUM,
    ):
        self._severity_by_type = {k.lower(): v for k, v in severity_by_type.items()}
        self._default = default_severity

    def evaluate(self, window: ShiftWindow, baseline: Baseline) -> list[Change]:
        return [
            Change(
                rule=self.name,
                summary=f"{incident.type.capitalize()} at {incident.time:%H:%M}: {incident.text}",
                severity=self._severity_by_type.get(incident.type.lower(), self._default),
                evidence=(incident.id,),
            )
            for incident in sorted(window.incidents, key=lambda i: i.time)
        ]
