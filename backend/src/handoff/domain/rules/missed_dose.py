"""Any dose missed, refused or held is a change (docs/PLAN.md, Handoff pipeline step 2)."""

from collections.abc import Mapping
from types import MappingProxyType

from handoff.domain.entities import Baseline, Change, MedAdministration, ShiftWindow
from handoff.domain.value_objects import MedStatus, Severity

DEFAULT_SEVERITY: Mapping[MedStatus, Severity] = MappingProxyType(
    {
        MedStatus.MISSED: Severity.HIGH,
        MedStatus.REFUSED: Severity.HIGH,
        MedStatus.HELD: Severity.MEDIUM,
    }
)


class MissedDoseRule:
    """One Change per medication that wasn't given, citing every affected eMAR record.

    Grouping by medication means "refused amlodipine twice" is one line with two
    sources, not two near-identical lines. Severity is the worst status seen.
    """

    name = "MissedDoseRule"

    def __init__(self, severity_by_status: Mapping[MedStatus, Severity] = DEFAULT_SEVERITY):
        if MedStatus.GIVEN in severity_by_status:
            raise ValueError("A given dose is not a change")
        self._severity = dict(severity_by_status)

    def evaluate(self, window: ShiftWindow, baseline: Baseline) -> list[Change]:
        by_med: dict[str, list[MedAdministration]] = {}
        for record in sorted(window.meds, key=lambda m: m.time):
            if record.status in self._severity:
                by_med.setdefault(record.med, []).append(record)

        return [self._change(med, records) for med, records in by_med.items()]

    def _change(self, med: str, records: list[MedAdministration]) -> Change:
        events = ", ".join(
            f"{r.status} at {r.time:%H:%M}" + (f" ({r.reason})" if r.reason else "")
            for r in records
        )
        severity = max((self._severity[r.status] for r in records), key=lambda s: s.rank)
        return Change(
            rule=self.name,
            summary=f"{med} {records[0].dose}: {events}",
            severity=severity,
            evidence=tuple(r.id for r in records),
        )
