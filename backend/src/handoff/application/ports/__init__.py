"""Ports (typing.Protocol) that adapters implement."""

from handoff.application.ports.clock import Clock
from handoff.application.ports.handoffs import HandoffStore
from handoff.application.ports.llm import HandoffWriter
from handoff.application.ports.records import ClinicalRecordReader, ResidentReader, ShiftReader
from handoff.application.ports.settings import SettingsStore

__all__ = [
    "ClinicalRecordReader",
    "Clock",
    "HandoffStore",
    "HandoffWriter",
    "ResidentReader",
    "SettingsStore",
    "ShiftReader",
]
