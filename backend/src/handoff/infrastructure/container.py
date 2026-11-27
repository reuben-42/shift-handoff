"""Composition root: the only module that constructs concrete classes.

It reads config, builds adapters and injects them into use cases.
Empty in the skeleton; wired up in step 07.
"""

from dataclasses import dataclass

from handoff.infrastructure.config import Settings


@dataclass
class Container:
    settings: Settings

    @classmethod
    def build(cls, settings: Settings) -> "Container":
        return cls(settings=settings)
