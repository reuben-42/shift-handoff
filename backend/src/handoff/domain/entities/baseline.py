"""A resident's normal: what "changed" is measured against."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median

from handoff.domain.entities.records import VitalSign

BASELINE_DAYS = 7
WEIGHT_LOOKBACK_DAYS = 30


@dataclass(frozen=True)
class Baseline:
    resident_id: str
    bp_sys: float | None = None
    bp_dia: float | None = None
    hr: float | None = None
    spo2: float | None = None
    temp_c: float | None = None
    pain_0_10: float | None = None
    reference_weight_kg: float | None = None

    @classmethod
    def from_vitals(
        cls, resident_id: str, history: Iterable[VitalSign], before: datetime
    ) -> "Baseline":
        """Medians over the 7 days before `before`; reference weight = earliest in 30 days.

        Only readings strictly before `before` count, so a shift's own readings
        never move the baseline they are compared with.
        """
        history = [v for v in history if v.resident_id == resident_id and v.time < before]
        recent = [v for v in history if v.time >= before - timedelta(days=BASELINE_DAYS)]
        weights = sorted(
            (
                v
                for v in history
                if v.weight_kg is not None
                and v.time >= before - timedelta(days=WEIGHT_LOOKBACK_DAYS)
            ),
            key=lambda v: v.time,
        )

        def med(field: str) -> float | None:
            values = [getattr(v, field) for v in recent if getattr(v, field) is not None]
            return float(median(values)) if values else None

        return cls(
            resident_id=resident_id,
            bp_sys=med("bp_sys"),
            bp_dia=med("bp_dia"),
            hr=med("hr"),
            spo2=med("spo2"),
            temp_c=med("temp_c"),
            pain_0_10=med("pain_0_10"),
            reference_weight_kg=weights[0].weight_kg if weights else None,
        )
