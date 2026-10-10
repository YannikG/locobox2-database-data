---
name: locobox-import
description: >-
  Orchestrate Locobox article import with tools/cli (uv run locobox): catalog
  extract, manual queue gate with the user, CloakBrowser shop fetch with jitter,
  shared YAML pipeline, agent logic checks via articles set-field/patch, and
  handoff. Prefer tools/cli over any legacy MCP import scripts. Use when
  importing catalog/shop articles or when this skill is attached.
---

# Locobox Import (Agent in der Mitte)

Der Agent **orchestriert** die Typer-CLI. Der User entscheidet am **Kuratier-Gate**, was importiert wird. Lange Fetches darf der User im eigenen Terminal starten; kurze Schritte kann der Agent selbst fahren, wenn der User das erlaubt.

## Setup

```bash
cd tools/cli && uv sync
uv run locobox --help
```

Repo-Root für Pfade: `articles/`, `rules/`, `config/tags/`, `.tmp/import/{campaign}/`.

## Ablauf (Pflicht)

### 0. Import-Tag (Agent fragt)

Agent fragt den User nach einem **Import-Tag** (empfohlen, CLI-optional), z. B. `piko-neuheiten-2020`.

```bash
uv run locobox tags ensure --slug IMPORT_TAG \
  --name "PIKO Neuheiten 2020" \
  --description "…"
```

Ohne Tag: Parse schreibt Artikel ohne neuen Tag. Unbekannter Tag → CLI failt mit Hinweis auf `tags ensure`.

### 1. Katalog → Kandidaten

```bash
uv run locobox catalog pdf-to-text --pdf PATH/katalog.pdf -o .tmp/piko_catalog.txt
uv run locobox catalog extract --source piko -t .tmp/piko_catalog.txt \
  --campaign CAMPAIGN --min-price-eur 120   # Preisfilter optional
uv run locobox queue show -a .tmp/import/CAMPAIGN/candidates.txt --limit 30
uv run locobox queue diff --mfr piko -a .tmp/import/CAMPAIGN/candidates.txt --campaign CAMPAIGN
```

Agent fasst zusammen: Anzahl, Missing vs. Repo, Preisband, Beispiele. **Kein Fetch ohne User-OK.**

### 2. Manuelles Gate (mit User)

Gemeinsam entscheiden, was rein soll. Dann:

```bash
uv run locobox queue approve \
  --candidates .tmp/import/CAMPAIGN/candidates.txt \
  --out .tmp/import/CAMPAIGN/approved.txt \
  --mfr piko --only-missing --campaign CAMPAIGN
  # optional: --min-price-eur … --include … --exclude …
```

### 3. Shop-Fetch (CloakBrowser, Jitter)

```bash
uv run locobox shop fetch --source SOURCE \
  -a .tmp/import/CAMPAIGN/approved.txt \
  --campaign CAMPAIGN \
  --delay-min 2.5 --delay-max 6.0
```

`SOURCE`: `piko` | `roco`.

- concurrency 1, `--skip-existing` default
- bei Block: stoppen, `.tmp/import/CAMPAIGN/blocked.txt` prüfen, ggf. Delay erhöhen / später Pro-Cloak
- **kein** Glass/`cursor-ide-browser` für Batches, **kein** Chrome-MCP-Import

### 4. Parse + shared Pipeline

```bash
uv run locobox shop parse --source SOURCE --campaign CAMPAIGN \
  --tag IMPORT_TAG
# Existing JSON: default skip (kein Overwrite). Nur Tag anhängen:
uv run locobox shop parse --source SOURCE --campaign CAMPAIGN \
  --tag IMPORT_TAG --append-tag-if-exists
# Oder ohne HTML, nur Tag auf Queue:
uv run locobox articles append-tag --mfr SOURCE --tag IMPORT_TAG \
  -a .tmp/import/CAMPAIGN/approved.txt
```

- Neu → Write inkl. Tag (wenn `--tag` gesetzt).
- Existiert ohne `--append-tag-if-exists` → `skipped_existing`.
- YAML-Rules: `rules/common/`, `rules/piko/`, `rules/roco/`.

### 5. Agent-Logikchecks

Stichproben / Kampagnen-Tag-Scope lesen. Domänenregeln und Pass-2: Skill **`lok-numbering-article-review`**.

Korrekturen **nicht** freestyle basteln, sondern:

```bash
uv run locobox articles set-field --mfr piko --article NR --path model.type --value "…"
# oder Batch:
uv run locobox articles patch -f changes.jsonl
uv run locobox articles validate --mfr piko --article NR
```

Danach `npm run check` (oder User dazu auffordern).

### 6. Clear / Neustart

```bash
uv run locobox pipeline clear --campaign CAMPAIGN --dry-run
uv run locobox pipeline clear --campaign CAMPAIGN --yes
# optional HTML: --html-cache
```

Löscht nur Working-State unter `.tmp/import/…`, nicht `articles/` oder `rules/`.

### 7. Handoff

```markdown
## Locobox Import

| Feld | Wert |
|------|------|
| **Hersteller** | PIKO \| Roco |
| **Import-Tag** | `{IMPORT_TAG}` \| ohne Tag |
| **Kampagne (Working-Dir)** | `{CAMPAIGN}` |
| **Branch** | `{branch}` |
| **Kandidaten / Approved** | `{N}` / `{M}` |
| **Fetch** | ok={OK} fail={FAIL} skipped={S} blocked={yes/no} |
| **JSON** | `{COUNT}` unter `articles/{piko\|roco}/` |
| **Pipeline/Rules** | {kurz} |
| **Logikchecks / patch** | {kurz} |
| **`npm run check`** | PASS \| FAIL |
| **Offen** | {missing shop, Pass-2, …} |
```

## Hard rules

1. **Gate vor Fetch** — ohne Approved-Queue und User-OK keinen `shop fetch`.
2. **Eine Pipeline nach Raw** — Fixes primär `rules/**/*.yaml`, dann `articles set-field`/`patch`.
3. **Agent entscheidet Tool-Reihenfolge**, erfindet aber keine parallele MCP-/Utils-Pipeline.
4. **Schweizer Text:** Umlaute, kein ß (Pipeline macht swiss-ss).
5. Keine parallele MCP-/Utils-Pipeline. Shop läuft nur über `shop fetch/parse --source piko|roco`.
6. **Auto-Tag:** User nach Tag fragen; vorher `tags ensure`; Existing nicht überschreiben (skip oder `--append-tag-if-exists` / `articles append-tag`).

## Verweise

- CLI: [`tools/cli/README.md`](../../../tools/cli/README.md)
- Rules: [`rules/README.md`](../../../rules/README.md)
- Domänen-Review: Skill `lok-numbering-article-review`
