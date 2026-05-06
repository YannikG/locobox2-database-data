# Data Contract

Diese Schemata sind die verbindliche Schnittstelle zwischen dem öffentlichen Data-Repository und der privaten Build-Pipeline.

## Enthaltene Schemata

- `article.schema.json` für einzelne Artikeldateien.
- `taxonomy-item.schema.json` für einzelne Kategorien-, Tags-, Massstab- und Stromsystem-Dateien.
- `manufacturer.schema.json` für optionale Hersteller-Metadaten pro Datei.

## Designregeln

- Contributor arbeiten mit einer Datei pro Artikel.
- Build-Prozesse transformieren die Rohdaten später in suchoptimierte Shards.
- Änderungen an den Schemata folgen Semver und müssen dokumentiert werden.
- **`model.number` / `model.livery`:** dürfen `null` sein, solange Splitt oder Lackname noch offen ist (siehe Agent-Skill Loknummerierung).
- **`releaseDate`:** `null`, ISO-Datum (`YYYY-MM-DD`), vierstelliges Jahr (`YYYY`) oder Freitext (z. B. «Frühling 2026» laut Hersteller).
- **Taxonomie-Slugs:** dürfen Grossbuchstaben enthalten (z. B. `H0`), damit sie mit `model.scale` und Tag-Werten übereinstimmen können.
- **`decoderInterfaces`:** optionales Feld **`aliases`** (Strings), die in Artikeln als Rohimport erlaubt sind; kanonisch bleiben `name` und `slug`.
- **`model.electricSystem`:** Im Artikelschema als **`enum`** geführt; Werte entsprechen den Taxonomie-Dateien unter `config/electric-systems/` (je `name` und, falls abweichend, `slug`, z. B. `Other` / `other`).
- Semantik-Checks ergänzen die Schemas, insbesondere für:
  - ID-Konvention (`{manufacturerSlug}-{articleNumber}`)
  - Referenzen auf Hersteller-Konfigurationen
  - Eindeutigkeit von Taxonomie-Slugs und -Namen pro Collection

## Rückwärtskompatibilität

- Patch: rein additive Korrekturen ohne Strukturbruch.
- Minor: neue optionale Felder (z. B. `source.imageUrl` für PDP-Produktbilder).
- Major: Breaking Changes mit Migrationspfad.

Details zu Pflichtkeys, `null` und `releaseDate` stehen in **`article.schema.json`** (Kommentare in `description` wo nötig).
