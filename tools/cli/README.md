# locobox CLI (`tools/cli`)

Typer/`uv`-CLI für den Artikel-Import. Agents und User nutzen dieselben Befehle.

## Setup

```bash
cd tools/cli
uv sync
uv run locobox --help
```

Python **≥ 3.13** (siehe `.python-version`).

## Queue (Gate)

Arbeitsstand: `.tmp/import/{campaign}/`.

```bash
uv run locobox queue normalize -a .tmp/raw.txt -o .tmp/import/demo/candidates.txt
uv run locobox queue show -a .tmp/import/demo/candidates.txt
uv run locobox queue diff --mfr piko -a .tmp/import/demo/candidates.txt --campaign demo
uv run locobox queue approve \
  --candidates .tmp/import/demo/candidates.txt \
  --out .tmp/import/demo/approved.txt \
  --mfr piko --only-missing --campaign demo
uv run locobox queue clear --campaign demo --dry-run
uv run locobox queue clear --campaign demo --yes
```

Fetch erst auf **Approved**-Queue.

## Catalog (PIKO)

```bash
uv run locobox catalog pdf-to-text --pdf ../../katalog.pdf -o .tmp/piko_catalog.txt
uv run locobox catalog extract --source piko -t .tmp/piko_catalog.txt \
  --campaign demo --min-price-eur 120
```

## Shop fetch + parse (PIKO / Roco / CloakBrowser)

```bash
# nach queue approve …
uv run locobox shop fetch --source piko \
  -a .tmp/import/demo/approved.txt \
  --campaign demo --delay-min 2.5 --delay-max 6.0

# Tag vorher in Taxonomy (wenn noch fehlend)
uv run locobox tags ensure --slug piko-neuheiten-2024

uv run locobox shop parse --source piko --campaign demo \
  --tag piko-neuheiten-2024 --dry-run
uv run locobox shop parse --source piko --campaign demo \
  --tag piko-neuheiten-2024

# Existing JSON: default skip. Nur Tag anhängen:
uv run locobox shop parse --source piko --campaign demo \
  --tag piko-neuheiten-2024 --append-tag-if-exists
uv run locobox articles append-tag --mfr piko --tag piko-neuheiten-2024 \
  -a .tmp/import/demo/approved.txt

# Roco (Magento catalogsearch → PDP)
uv run locobox shop fetch --source roco \
  -a .tmp/import/demo/approved.txt \
  --campaign demo --delay-min 2.5 --delay-max 6.0
uv run locobox shop parse --source roco --campaign demo \
  --tag roco-neuheiten-2024
```

`--source`: `piko` | `roco`. `--tag` optional (Alias `--campaign-tag`). Unbekannter Tag → Exit ≠ 0. Existing ohne `--append-tag-if-exists` → skip. Bei Block: Exit ≠ 0 und `.tmp/import/{campaign}/blocked.txt`.

## Pipeline + YAML-Rules

Rules liegen im Repo unter [`rules/`](../../rules/). Nach dem Laden von Raw-Artikeln:

```bash
# Dry-run
uv run locobox pipeline apply --dir ../../articles/piko --dry-run

# Anwenden
uv run locobox pipeline apply --file ../../articles/piko/21002.json

uv run locobox pipeline clear --campaign demo --dry-run
```

Rule-Shape (Beispiel):

```yaml
rules:
  - id: piko-strip-inkl-sound-decoder
    when:
      manufacturer: piko
      field: model.type
      match: "(?i),?\\s*inkl\\.?\\s*PIKO Sound-?Decoder.*$"
    then:
      replace: ""
```

Aktionen: `replace`, `set` (+ optional `set_field`), `clear`, `add_to_list`.

## Articles (Agent-Edits)

```bash
uv run locobox articles validate --mfr piko --article 21002

uv run locobox articles set-field \
  --mfr piko --article 21002 \
  --path model.type --value "BR E410" \
  --dry-run

# Batch JSONL: {"mfr":"piko","article":"21002","path":"model.type","value":"BR E410"}
uv run locobox articles patch -f changes.jsonl --dry-run
```

Nach jedem Write: Schema-Check gegen `contracts/article.schema.json`. Optional Audit: `.tmp/article-patch-audit.jsonl`.

## Architektur

Onion × Feature-Slices unter `src/locobox_cli/`:

- `domain/` — Value Objects
- `application/` — Use Cases + Ports (eine Pipeline nach Raw)
- `adapters/` — FS, YAML-Rules, CloakBrowser, Shop sources (`piko` / `roco`)
- `interfaces/cli/` — Typer

## Tests

```bash
cd tools/cli
uv run pytest
```
