"""Application errors. Adapters translate them into HTTP codes."""


class AppError(Exception):
    """Base class for errors a caller can act on."""


class ResidentNotFound(AppError):
    def __init__(self, resident_id: str):
        super().__init__(f"Resident {resident_id!r} not found")


class HandoffNotFound(AppError):
    def __init__(self, resident_id: str, shift_id: str):
        super().__init__(f"No handoff for {resident_id!r} on shift {shift_id!r}")


class SourceNotFound(AppError):
    def __init__(self, source_id: str):
        super().__init__(f"Source record {source_id!r} not found")


class InvalidShift(AppError):
    pass


class InvalidShiftPattern(AppError):
    pass
