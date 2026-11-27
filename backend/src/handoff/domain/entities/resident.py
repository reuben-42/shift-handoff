from dataclasses import dataclass


@dataclass(frozen=True)
class Resident:
    id: str
    name: str
    room: str
    age: int
    conditions: tuple[str, ...] = ()
    allergies: tuple[str, ...] = ()
    active_meds: tuple[str, ...] = ()
    code_status: str = "Full code"

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Resident needs an id")
        if self.age < 0:
            raise ValueError("Age cannot be negative")
