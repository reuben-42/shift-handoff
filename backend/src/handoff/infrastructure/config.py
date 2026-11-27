"""Settings read from environment variables. Filled in as steps need them."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    db_path: str
    shift_pattern: str
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "fake"),
            db_path=os.getenv("DB_PATH", "../data/handoff.sqlite"),
            shift_pattern=os.getenv("SHIFT_PATTERN", "3x8"),
            cors_origins=tuple(
                o.strip()
                for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
                if o.strip()
            ),
        )
