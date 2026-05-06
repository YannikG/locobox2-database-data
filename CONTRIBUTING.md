# Beitrag zur Locobox Community-Datenbank

Danke für deinen Beitrag.

## Schnellstart

1. Fork erstellen.
2. Neue Datei unter `articles/{manufacturerSlug}/` anlegen.
3. Schema aus `contracts/article.schema.json` einhalten.
4. Lokal prüfen mit `npm ci` und `npm run check` (Node 22 empfohlen).
5. Pull Request mit kurzer Quellenangabe öffnen.

## Wichtigste Regeln

- Eine Datei pro Artikel.
- IDs und Slugs nur in Kleinbuchstaben mit Bindestrichen.
- Felder `manufacturer`, `articleNumber`, `releaseDate`, `uvp` und `model` sind Pflicht.
- Im `model` sind auch `scale`, `electricSystem` und `era` Pflicht.
- Features werden unter `model.features` als Liste gepflegt, z. B. `Analog`, `Digital`, `Sound`.
- Lüp wird als `model.luepMm` in Millimeter gepflegt.
- Mindestradius wird als `model.minRadiusMm` in Millimeter gepflegt.
- Optional: `model.decoderInterface`, `model.variantGroup`, `model.couplerSystem`, `identifiers.ean`.
- `description` darf frei formuliert werden und kann leer bleiben.
- `source.url` sollte für neue oder geänderte Fakten angegeben werden.
- Optional: `source.imageUrl` (HTTPS) für die URL des **Produktbilds**, üblicherweise von derselben Quelle wie `source.url`.

## AI-unterstützte Beiträge

- AI darf verwendet werden.
- Vor dem PR bitte immer Fakten prüfen.
- Quellen sollen im Feld `source.url` dokumentiert werden.

## Lokale Qualitätssicherung

Vor dem Öffnen eines Pull Requests:

- `npm ci`
- `npm run check` (Lint, Format, Tests, Schema- und Semantikprüfung, Suchindex, Artefakt-Check)

Die CI führt denselben Ablauf im Workflow **Validate Data** bei Pull Requests und bei Pushes auf `master` aus.

## Dateibenennung

Empfehlung: `articles/{manufacturerSlug}/{articleNumber}.json`, Beispiel `articles/roco/79824.json`.

## Hersteller-Konfiguration

Optional kann pro Hersteller eine Datei unter `config/manufacturers/{slug}.json` gepflegt werden, z. B. mit Logo-Link, Website, Beschreibung und Wikipedia-Link.

## Kategorien, Tags, Massstab, Stromsystem und Features

Jeder Eintrag hat eine eigene Datei mit `description`:

- `config/categories/{slug}.json`
- `config/tags/{slug}.json`
- `config/scales/{slug}.json`
- `config/electric-systems/{slug}.json`
- `config/features/{slug}.json`
