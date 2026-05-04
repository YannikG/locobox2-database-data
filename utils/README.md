# Hilfsprogramme (`utils/`)

Python-Skripte für Datenpflege (Roco **Shop**: PDP-Parser und optional Chrome-MCP-Import). Abhängigkeiten liegen zentral in **`requirements.txt`** in diesem Ordner. Paket **`mcp`** ist nur für **Python 3.10+** vorgesehen (PEP-508-Marker).

## Virtuelle Umgebung

Im **Repository-Root** (nicht innerhalb von `utils/`):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r utils/requirements.txt
```

**Python:** mindestens **3.10** für `pip install -r utils/requirements.txt` und **`roco_mcp_chrome_search_import.py`**. Empfohlen: **3.12+** (z. B. Homebrew `python@3.12` / `python@3.13`).

## Wichtige Skripte

| Pfad | Zweck |
|------|--------|
| `roco/shop-pdp-parse/roco_shop_parse_pdp.py` | PDP-HTML parsen und JSON mergen; optional **`--image-url`** (z. B. vom MCP-Skript); **`--url`** nur für Reparatur/HTTP ohne Browser-Session (nicht parallel zum Chrome-MCP-Shopflow) |
| `roco/shop-pdp-parse/roco_mcp_chrome_search_import.py` | Shop-Suche + PDP in Chrome (stdio-MCP): **`--mcp-from-cursor`** liest `~/.cursor/mcp.json`; **`--no-network-image`** schaltet `list_network_requests` ab; Standard **`--isolated`** am Chrome-MCP (siehe `--help`) |

Nach `activate` immer mit `python …` aus dem Repo-Root aufrufen, damit Pfade stimmen.

## Unit Tests

Siehe **[`TESTING.md`](TESTING.md)** (Ausführung mit `unittest`, Ablage der `test_*.py`-Dateien, Konventionen).

### Artikel ohne `source.imageUrl` (Liste für MCP-Batch)

Neu erzeugen (alle `articles/roco/*.json` ohne nicht leeres `source.imageUrl` → `.tmp/articles-missing-imageurl.txt`):

```bash
python3 <<'PY'
import json
from pathlib import Path
root, out = Path("articles/roco"), Path(".tmp/articles-missing-imageurl.txt")
missing = []
for p in sorted(root.glob("*.json"), key=lambda x: x.name):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        continue
    s = d.get("source")
    img = s.get("imageUrl") if isinstance(s, dict) else None
    if not (isinstance(img, str) and img.strip()):
        missing.append(p.stem)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(missing) + ("\n" if missing else ""), encoding="utf-8")
print(len(missing), "→", out)
PY
```

## Deaktivieren

```bash
deactivate
```

Der Ordner `.venv/` ist in `.gitignore` eingetragen.
