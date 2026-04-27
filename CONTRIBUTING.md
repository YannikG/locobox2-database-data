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
- Im `model` sind auch `scale`, `electricSystem` und `era` Pflicht.
- Features werden unter `model.features` als Liste gepflegt, z. B. `Analog`, `Digital`, `Sound`.
- LüP wird als `model.luepMm` in Millimeter gepflegt.
- Mindestradius wird als `model.minRadiusMm` in Millimeter gepflegt.
- Optional: `model.decoderInterface`, `model.variantGroup`, `model.couplerSystem`, `identifiers.ean`.
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
