from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Manufacturer(str, Enum):
    PIKO = "piko"
    ROCO = "roco"

    @classmethod
    def parse(cls, raw: str) -> Manufacturer:
        key = raw.strip().lower()
        try:
            return cls(key)
        except ValueError as exc:
            allowed = ", ".join(m.value for m in cls)
            raise ValueError(f"unknown manufacturer {raw!r}; expected one of: {allowed}") from exc

    @property
    def display_name(self) -> str:
        return {
            Manufacturer.PIKO: "PIKO",
            Manufacturer.ROCO: "Roco",
        }[self]

    @property
    def slug(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ManufacturerRef:
    """Optional free-form manufacturer until more than the allowlist exist."""

    slug: str

    @classmethod
    def from_manufacturer(cls, mfr: Manufacturer) -> ManufacturerRef:
        return cls(slug=mfr.slug)
