# locobox2-database-data

Öffentliches Datenrepository für Locobox.

## Struktur

- `articles/`: Artikeldaten, eine Datei pro Artikelnummer.
- `config/`: Taxonomie und Stammdaten (`categories`, `scales`, `tags`, `features`, `electric-systems`, `decoder-interfaces`, `manufacturers`).
- `contracts/`: Verbindliche JSON-Schemas und Data-Contract-Dokumentation.
- `utils/`: Python-Hilfsprogramme (Roco PDP/MCP unter `utils/roco/shop-pdp-parse/`), siehe `utils/README.md` und `utils/requirements.txt`.
- `.agents/skills/caveman/`: optionaler Agent-Skill (kurze Kommunikation).

## Einstieg

- Git-Hooks: [Husky](https://typicode.github.io/husky/) mit Pre-Commit (**Prettier** auf gestagete Dateien via **lint-staged**); nach `npm ci` aktiv.
- Regeln für Beiträge: `CONTRIBUTING.md`
- Contract-Details: `contracts/README.md`
- Python-Tools und venv: `utils/README.md`
