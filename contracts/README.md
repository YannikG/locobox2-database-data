# Data Contract

Diese Schemata sind die verbindliche Schnittstelle zwischen dem öffentlichen Daten-Repository und der privaten Build-Pipeline.

## Schemata

- `article.schema.json` – einzelne Artikeldateien.
- `taxonomy-item.schema.json` – Kategorien, Tags, Massstab, Stromsystem.
- `manufacturer.schema.json` – optionale Hersteller-Metadaten pro Datei.

## Designregeln

- Beitragende arbeiten mit einer Datei pro Artikel.
- Build-Prozesse können Rohdaten später in suchoptimierte Shards transformieren.
- Schemaänderungen folgen Semver und werden dokumentiert.
- **`model.number` / `model.livery`:** dürfen `null` sein, solange Splitt oder Lackname noch offen ist (siehe Agent-Skill Loknummerierung).
- **`releaseDate`:** `null`, ISO-Datum (`YYYY-MM-DD`), vierstelliges Jahr (`YYYY`) oder Freitext (z. B. «Frühling 2026» laut Hersteller).
- **Taxonomie-Slugs:** dürfen Grossbuchstaben enthalten (z. B. `H0`), damit sie mit `model.scale` und Tag-Werten übereinstimmen können.
- **`decoderInterfaces`:** optionales Feld **`aliases`** (Strings) für Rohimporte in Artikeln; kanonisch bleiben `name` und `slug`.
- **`model.electricSystem`:** im Artikelschema als **`enum`**; Werte entsprechen den Dateien unter `config/electric-systems/` (`name` und ggf. abweichender `slug`, z. B. `Other` / `other`).
- Semantik-Checks ergänzen die Schemas (u. a. ID `{manufacturerSlug}-{articleNumber}`, Referenzen auf Hersteller-Konfigurationen, Eindeutigkeit von Taxonomie-Slugs und -Namen pro Collection).

## Rückwärtskompatibilität

- **Patch:** rein additive Korrekturen ohne Strukturbruch.
- **Minor:** neue optionale Felder (z. B. `source.imageUrl` für PDP-Produktbilder).
- **Major:** Breaking Changes mit Migrationspfad.

Pflichtkeys, `null` und `releaseDate` sind in **`article.schema.json`** beschrieben (`description` in den betroffenen Properties).
