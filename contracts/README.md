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
- Semantik-Checks ergänzen die Schemas, insbesondere für:
  - ID-Konvention (`{manufacturerSlug}-{articleNumber}`)
  - Referenzen auf Hersteller-Konfigurationen
  - Eindeutigkeit von Taxonomie-Slugs und -Namen pro Collection

## Rückwärtskompatibilität

- Patch: rein additive Korrekturen ohne Strukturbruch.
- Minor: neue optionale Felder.
- Major: Breaking Changes mit Migrationspfad.
