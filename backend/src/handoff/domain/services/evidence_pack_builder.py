"""Builds the evidence pack: one compact line per record, e.g. `[V231] 14:35 BP 98/60 HR 88`."""

from collections.abc import Sequence

from handoff.domain.entities import (
    Baseline,
    Change,
    EvidenceLine,
    EvidencePack,
    Incident,
    MedAdministration,
    Note,
    Order,
    ShiftWindow,
    SourceRecord,
    VitalSign,
)


def _format_vital(v: VitalSign) -> str:
    parts = []
    if v.bp_sys is not None and v.bp_dia is not None:
        parts.append(f"BP {v.bp_sys}/{v.bp_dia}")
    elif v.bp_sys is not None:
        parts.append(f"SBP {v.bp_sys}")
    if v.hr is not None:
        parts.append(f"HR {v.hr}")
    if v.spo2 is not None:
        parts.append(f"SpO2 {v.spo2}%")
    if v.temp_c is not None:
        parts.append(f"T {v.temp_c:.1f}C")
    if v.rr is not None:
        parts.append(f"RR {v.rr}")
    if v.pain_0_10 is not None:
        parts.append(f"Pain {v.pain_0_10}/10")
    if v.weight_kg is not None:
        parts.append(f"Wt {v.weight_kg:.1f}kg")
    return " ".join(parts) or "vitals recorded (no values)"


def _format(record: SourceRecord) -> str:
    match record:
        case VitalSign():
            body = _format_vital(record)
        case MedAdministration():
            reason = f" ({record.reason})" if record.reason else ""
            body = f"{record.med} {record.dose} {record.status.upper()}{reason}"
        case Note():
            body = f"{record.author_role} note: {record.text}"
        case Order():
            body = f"New order ({record.type}): {record.text}"
        case Incident():
            body = f"Incident ({record.type}): {record.text}"
    return f"{record.time:%H:%M} {body}"


class EvidencePackBuilder:
    def build(
        self, window: ShiftWindow, baseline: Baseline, changes: Sequence[Change]
    ) -> EvidencePack:
        return EvidencePack(
            resident=window.resident,
            shift=window.shift,
            baseline=baseline,
            lines=tuple(EvidenceLine(r.id, _format(r)) for r in window.chronological()),
            changes=tuple(changes),
        )
