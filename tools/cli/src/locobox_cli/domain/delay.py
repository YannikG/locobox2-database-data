from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DelayPolicy:
    """Random wait between shop actions to reduce rate-limit risk."""

    min_seconds: float = 2.5
    max_seconds: float = 6.0

    def __post_init__(self) -> None:
        if self.min_seconds < 0 or self.max_seconds < self.min_seconds:
            raise ValueError("invalid delay range")

    def next_seconds(self) -> float:
        if self.min_seconds == self.max_seconds:
            return self.min_seconds
        return random.uniform(self.min_seconds, self.max_seconds)
