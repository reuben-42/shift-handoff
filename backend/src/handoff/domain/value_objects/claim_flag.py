from enum import StrEnum


class ClaimFlag(StrEnum):
    """Set by the verifier. Flagged claims render amber in the UI."""

    PARTIALLY_SUPPORTED = "partially_supported"
