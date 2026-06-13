# Triebfahrzeug-Formate und Locobox (Kurzfassung)

| Thema | Interner Auszug |
|--------|-----------------|
| **Parsing / Split `model.type` & `model.number`** | [internal/field-parsing-model.md](internal/field-parsing-model.md) |
| **Modell-`electricSystem` (DC/AC am Modell)** | [internal/field-parsing-model.md](internal/field-parsing-model.md) → «Modell-Stromsystem» |
| **PIKO Shop-Titel-Artefakte** | [internal/wiki-piko-shop-parsing.md](internal/wiki-piko-shop-parsing.md) |
| **Privatbahn → Land (Livery-Anker)** | [internal/wiki-privatbahn-livery-anker.md](internal/wiki-privatbahn-livery-anker.md) |
| Deutschland DB AG Baureihen | [internal/wiki-db-baureihen-liste.md](internal/wiki-db-baureihen-liste.md) |
| Österreich ÖBB | [internal/wiki-oebb-loks-liste.md](internal/wiki-oebb-loks-liste.md) |
| Schweiz | [internal/wiki-schweizer-bauartbezeichnungen.md](internal/wiki-schweizer-bauartbezeichnungen.md) |
| 12-stellig EVN | [internal/wiki-eindeutige-fahrzeugnummer.md](internal/wiki-eindeutige-fahrzeugnummer.md) |

## Locobox-Felder (nach Parsing)

- `model.type`: oft Baureihe oder **Reihe** (Präfix möglich).
- `model.number`: laufende Nummer, Untereinheit, oder Prüfziffer-Gruppe, je nach Konvention.
- `model.electricSystem`: **Modell** Gleich-/Wechselstrom und Analog/Digital (Enum), nicht Prototyp-kV — siehe [internal/field-parsing-model.md](internal/field-parsing-model.md).
- `model.country` / `model.operator`: nach Split prüfen (z. B. ÖBB → `AT` plausibel); PIKO «Privatbahn» → [internal/wiki-privatbahn-livery-anker.md](internal/wiki-privatbahn-livery-anker.md).
- `description` / `source.url`: Primärquelle für korrektes Splitting.
