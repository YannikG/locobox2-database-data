# locobox2-database-data

[![Validate Data](https://github.com/YannikG/locobox2-database-data/actions/workflows/validate-data.yml/badge.svg)](https://github.com/YannikG/locobox2-database-data/actions/workflows/validate-data.yml)
[![Dispatch private database submodule sync](https://github.com/YannikG/locobox2-database-data/actions/workflows/dispatch-private-database-sync.yml/badge.svg)](https://github.com/YannikG/locobox2-database-data/actions/workflows/dispatch-private-database-sync.yml)

Öffentliches Datenrepository für Locobox.

## Ordnerstruktur

- `articles/` – Artikeldaten, eine JSON-Datei pro Artikel.
- `config/` – Taxonomie und Stammdaten (`categories`, `scales`, `tags`, `features`, `electric-systems`, `decoder-interfaces`, `manufacturers`).
- `contracts/` – verbindliche JSON-Schemas und Erläuterungen, siehe [`contracts/README.md`](contracts/README.md).
- `utils/` – Python-Hilfsprogramme (z. B. Roco-Shop-PDP), siehe [`utils/README.md`](utils/README.md).

## Mitarbeit und Qualität

Richtlinien: [`CONTRIBUTING.md`](CONTRIBUTING.md).

Nach `npm ci` aktiviert [Husky](https://typicode.github.io/husky/) Git-Hooks: beim Commit formatiert **lint-staged** mit **Prettier** die **vorgemerkten** Dateien. Lint und Datenvalidierung laufen dort nicht automatisch; vor dem Push **`npm run check`** ausführen (gleicher Ablauf wie in der CI **Validate Data**).

Der Workflow **Dispatch private database submodule sync** dient der internen Synchronisation mit dem privaten Datenbank-Repository und betrifft normale Daten-PRs in der Regel nicht.
