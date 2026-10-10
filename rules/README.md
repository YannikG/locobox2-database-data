# Fix-Rules (YAML)

Deterministische Korrekturen für die shared Import-Pipeline (`locobox pipeline apply`).

- `common/` — herstellerübergreifend
- `piko/`, `roco/` — herstellerspezifisch

Ids müssen global eindeutig sein. Regex in `when.match` ist erlaubt. Komplexe Domänen-Splits bleiben Agent Pass-2 (`articles set-field` / Loknummer-Skill).
