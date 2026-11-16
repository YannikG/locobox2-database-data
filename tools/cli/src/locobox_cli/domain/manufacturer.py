from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Manufacturer(str, Enum):
    PIKO = "piko"
    ROCO = "roco"
    TRIX = "trix"
    REE = "ree"
    LSMODELS = "lsmodels"
    JOUEF = "jouef"
    BEMO = "bemo"
    ACME = "acme"

    @classmethod
    def parse(cls, raw: str) -> Manufacturer:
        key = raw.strip().lower()
        compact = key.replace(" ", "").replace(".", "").replace("-", "")
        if compact in {"lsmodels", "lsmodel"}:
            key = "lsmodels"
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
            Manufacturer.TRIX: "Trix",
            Manufacturer.REE: "REE",
            Manufacturer.LSMODELS: "LS Models",
            Manufacturer.JOUEF: "Jouef",
            Manufacturer.BEMO: "BEMO",
            Manufacturer.ACME: "ACME",
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
