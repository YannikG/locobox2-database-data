# Beitrag zur Locobox Community-Datenbank

Danke für deinen Beitrag.

## Schnellstart

1. Neue Datei unter `articles/{manufacturerSlug}/` anlegen.
2. Schema aus `contracts/article.schema.json` einhalten.
3. Pull Request mit kurzer Quellenangabe öffnen.

## Wichtigste Regeln

- Eine Datei pro Artikel.
- IDs und Slugs nur in Kleinbuchstaben mit Bindestrichen.
- Felder `manufacturer`, `articleNumber`, `releaseDate`, `uvp` und `model` sind Pflicht.
- Im `model` müssen die Keys laut Schema **vorkommen**; fehlende oder unbekannte Werte werden mit **`null`** gepflegt (z. B. `country`, `era`, `electricSystem`, `luepMm`, `minRadiusMm`). Bekannte Texte trotzdem setzen, wo die Quelle sie liefert.
- `releaseDate`: üblich ist die **Jahreszahl** (`"2026"`) oder ein volles Datum (`"2026-04-27"`), siehe `contracts/article.schema.json`.
- Features werden unter `model.features` als Liste gepflegt, z. B. `Analog`, `Digital`, `Sound` (Feld optional).
- LüP als `model.luepMm` in Millimeter (`null`, wenn unbekannt).
- Mindestradius als `model.minRadiusMm` in Millimeter (`null`, wenn unbekannt).
- Optional: `model.decoderInterface`, `model.variantGroup`, `model.couplerSystem`, `identifiers.ean`, `source.imageUrl`.
- `description` darf frei formuliert werden und kann leer bleiben.
- `source.url` sollte für neue oder geänderte Fakten angegeben werden.

## Taxonomie und Stammdaten

Taxonomie-Dateien liegen unter `config/`:

- `config/categories/`
- `config/tags/`
- `config/scales/`
- `config/electric-systems/`
- `config/features/`
- `config/decoder-interfaces/`
- `config/manufacturers/`

Jede Datei folgt entweder `contracts/taxonomy-item.schema.json` oder `contracts/manufacturer.schema.json`.

## AI-unterstützte Beiträge

- AI darf verwendet werden.
- Vor dem PR bitte immer Fakten prüfen.
- Quellen sollen im Feld `source.url` dokumentiert werden.
