from datetime import date, datetime

import pytest

from handoff.application.services import ActivePattern, EvidenceGatherer, HandoffVerifier
from handoff.application.use_cases import GenerateHandoff, GetUnitBoard
from handoff.domain.entities import Incident, MedAdministration, Note, Resident, VitalSign
from handoff.domain.rules import IncidentRule, MissedDoseRule
from handoff.domain.services import (
    ChangeDetector,
    CitationVerifier,
    CoverageGuard,
    EvidencePackBuilder,
    PriorityCalculator,
    ShiftCalendar,
)
from handoff.domain.value_objects import THREE_EIGHT, MedStatus, SourceId
from tests.fakes import (
    FakeHandoffWriter,
    FixedClock,
    InMemoryClinicalRecordReader,
    InMemoryHandoffStore,
    InMemoryResidentReader,
    InMemorySettingsStore,
)

DAY_SHIFT = "2026-12-03-day"


def at(hour: int, minute: int = 0, day: int = 3) -> datetime:
    return datetime(2026, 12, day, hour, minute)


RESIDENTS = [
    Resident("R01", "Ada Byrne", "2B-01", 88),
    Resident("R02", "Ben Okafor", "2B-02", 79),
    Resident("R03", "Cora Lind", "2B-03", 91),
]

RECORDS = [
    # R01: unwitnessed fall in the afternoon (high) + note about it
    Incident(SourceId("I12"), "R01", at(14, 20), "fall", "found on floor beside bed"),
    Note(SourceId("N88"), "R01", at(14, 30), "RN", "pt found on floor, no visible injury"),
    VitalSign(SourceId("V231"), "R01", at(14, 35), bp_sys=98, bp_dia=60, hr=88, spo2=95),
    VitalSign(SourceId("V100"), "R01", at(9, day=2), bp_sys=130, bp_dia=80),
    # R02: quiet shift
    VitalSign(SourceId("V232"), "R02", at(9), bp_sys=124, bp_dia=76),
    # R03: held dose (medium), and an evening refusal (outside the day shift)
    MedAdministration(SourceId("M5"), "R03", at(8), "metoprolol", "25 mg", MedStatus.HELD, "HR 52"),
    MedAdministration(SourceId("M6"), "R03", at(17), "metoprolol", "25 mg", MedStatus.REFUSED),
]


class World:
    """All the fakes and real domain services, wired like the composition root will."""

    def __init__(self, writer: FakeHandoffWriter | None = None):
        self.residents = InMemoryResidentReader(RESIDENTS)
        self.records = InMemoryClinicalRecordReader(RECORDS)
        self.store = InMemoryHandoffStore()
        self.settings = InMemorySettingsStore()
        self.writer = writer or FakeHandoffWriter()
        self.calendar = ShiftCalendar()
        self.pattern = ActivePattern(self.settings, default=THREE_EIGHT)
        self.gatherer = EvidenceGatherer(self.records)
        self.detector = ChangeDetector([MissedDoseRule(), IncidentRule()])
        self.verifier = HandoffVerifier(
            CitationVerifier(), CoverageGuard(), PriorityCalculator(), FixedClock()
        )

    def generate(self) -> GenerateHandoff:
        return GenerateHandoff(
            self.residents,
            self.gatherer,
            self.detector,
            EvidencePackBuilder(),
            self.writer,
            self.verifier,
            self.store,
            self.pattern,
            self.calendar,
        )

    def board(self) -> GetUnitBoard:
        return GetUnitBoard(
            self.residents,
            self.gatherer,
            self.detector,
            PriorityCalculator(),
            self.store,
            self.pattern,
            self.calendar,
        )


@pytest.fixture
def world() -> World:
    return World()


__all__ = ["DAY_SHIFT", "World", "at", "date"]
