# Beitrag zur Locobox Community-Datenbank

Danke für deinen Beitrag.

## Schnellstart

1. Fork erstellen.
2. Neue Datei unter `articles/{manufacturerSlug}/` anlegen (eine Datei pro Artikel).
3. Schema aus `contracts/article.schema.json` einhalten.
4. Lokal: `npm ci`, danach `npm run check` (Node 22 empfohlen).
5. Pull Request mit kurzer Quellenangabe öffnen.

## Git-Hooks

Nach `npm ci` setzt das Skript **`prepare`** [Husky](https://typicode.github.io/husky/) auf (`core.hooksPath`). Beim **`git commit`** läuft nur **lint-staged** (**Prettier** auf vorgemerkte, nicht ignorierte Dateien). **`npm run lint`** und **`npm run validate:data`** laufen dort nicht. Vor dem Push wie in der CI **`npm run check`** ausführen (oder einzeln `lint` / `validate:data`). Hook auslassen: **`git commit --no-verify`**.

## Wichtigste Regeln

- IDs und Slugs nur in Kleinbuchstaben mit Bindestrichen.
- Pflichtfelder: `manufacturer`, `articleNumber`, `releaseDate`, `uvp`, `model`.
- Im Objekt `model` sind zwingend `scale`, `electricSystem` und `era` gesetzt.
- Features unter `model.features` als Liste, z. B. `Analog`, `Digital`, `Sound`.
- Lüp als `model.luepMm` in Millimetern; Mindestradius als `model.minRadiusMm`.
- Optional: `model.decoderInterface`, `model.variantGroup`, `model.couplerSystem`, `identifiers.ean`.
- `description` frei formuliert, darf leer sein.
- `source.url` bei neuen oder geänderten Fakten setzen.
- Optional: `source.imageUrl` (HTTPS) für das Produktbild, üblicherweise dieselbe Quelle wie `source.url`.

## KI-unterstützte Beiträge

KI darf genutzt werden. Vor dem PR Fakten prüfen und in `source.url` belegen.

## Dateibenennung

`articles/{manufacturerSlug}/{articleNumber}.json`, z. B. `articles/roco/79824.json`.

## Hersteller-Konfiguration

Optional: `config/manufacturers/{slug}.json` (Logo, Website, Beschreibung, Wikipedia-Link).

## Taxonomie-Dateien

Je Eintrag eine Datei mit `description`:

- `config/categories/{slug}.json`
- `config/tags/{slug}.json`
- `config/scales/{slug}.json`
- `config/electric-systems/{slug}.json`
- `config/features/{slug}.json`
