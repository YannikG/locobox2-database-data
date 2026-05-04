# locobox2-database-data

Öffentliches Datenrepository für Locobox.

## Struktur

- `articles/`: Artikeldaten, eine Datei pro Artikelnummer.
- `config/`: Taxonomie und Stammdaten (`categories`, `scales`, `tags`, `features`, `electric-systems`, `decoder-interfaces`, `manufacturers`).
- `contracts/`: Verbindliche JSON-Schemas und Data-Contract-Dokumentation.
- `utils/`: Python-Hilfsprogramme (Roco PDP/MCP unter `utils/roco/shop-pdp-parse/`), siehe `utils/README.md` und `utils/requirements.txt`.
- `.agents/skills/`: Agent-Skills für Datenextraktion und Pflege.

## Einstieg

- Regeln für Beiträge: `CONTRIBUTING.md`
- Contract-Details: `contracts/README.md`
- Python-Tools und venv: `utils/README.md`
