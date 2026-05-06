# Unit Tests (`utils/`)

Die Python-Hilfsprogramme unter `utils/` nutzen die **Standardbibliothek** [`unittest`](https://docs.python.org/3/library/unittest.html). Es ist **kein** pytest oder anderes Test-Framework nötig.

## Voraussetzungen

- **Python 3.10+** (wie für `utils/requirements.txt` und die Skripte).
- Virtuelle Umgebung optional; für reine Parser-Tests reicht oft das System-`python3`.

## Tests ausführen

Im **Repository-Root** (nicht innerhalb von `utils/`):

```bash
python3 -m unittest discover -s utils/roco/shop-pdp-parse -p 'test_*.py' -v
```

Einzelne Testdatei (Ordnername enthält einen Bindestrich, daher weiter mit `discover`):

```bash
python3 -m unittest discover -s utils/roco/shop-pdp-parse -p 'test_roco_shop_parse_pdp.py' -v
```

Alternativ im Ordner `utils/roco/shop-pdp-parse/`:

```bash
cd utils/roco/shop-pdp-parse && python3 -m unittest test_roco_shop_parse_pdp -v
```

**`discover` mit `-s`** setzt das Startverzeichnis so, dass `import roco_shop_parse_pdp` aus den Tests klappt.

## Wo Tests liegen

| Bereich | Verzeichnis | Dateien |
|---------|-------------|---------|
| Roco Shop PDP / Merge | `utils/roco/shop-pdp-parse/` | `test_*.py` (z. B. `test_roco_shop_parse_pdp.py`) |

Neue Tests für andere Unterordner von `utils/`: entweder gleiches Muster (`discover` mit passendem `-s`) oder später ein gemeinsames `utils/tests/`-Paket, dann Importpfade anpassen.

## Konventionen

- Testklassen: `Test…`, Methoden: `test_…`.
- Keine Netzwerkaufrufe in Unit-Tests, wenn möglich (fixtures, temporäre Verzeichnisse, kurze HTML-Strings).
- Öffentliche Hilfsfunktionen testen; private Funktionen (`_name`) nur, wenn sie stabil genug sind und sonst zu viel Logik ungetestet bliebe.
