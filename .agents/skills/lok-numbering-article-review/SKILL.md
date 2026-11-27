---
name: lok-numbering-article-review
description: >-
  Two-phase Locobox article JSON review plus optional auto-fix: (0) on request,
  apply whitelisted splits (prefer Python helpers under
  .agents/skills/lok-numbering-article-review/scripts/, especially
  autofix_model_type_number_split.py for type/number splitting), livery/era fixes, and same-rule fixes to sibling
  variant articles when present in repo (per manufacturer rules in skill docs);
  country only when unambiguous. (1) full pass with findings, (2) one file at a
  time user resolves (skip / ignore). Read-only unless auto-fix or explicit edit
  order. Re-review of ignored items only when user explicitly asks. Use for
  Loknummer review or when this skill is attached.
disable-model-invocation: true
---

# Loknummerierung: Parsing, Split, Plausibilität (zwei Phasen)

## Hauptziel

1. **Parsen und splitten:** Aus `model.type` (und bei Bedarf `description`, `source.url`, `model.number`) Baureihe/Reihe vs laufende Nummer ableiten.
2. **Plausibilität:** Abgleich mit Operator, Land, **Stromsystem** (`model.electricSystem` vs. Beschreibung und vs. **Schwester-Varianten** derselben Baureihe laut Hersteller-Logik, siehe unten), **`scale`** (Schema: u. a. `H0`, nicht `h0`), **Kategorien** vs. Baureihe (z. B. Diesellok vs. `elektrolokomotive`), Fliesstext, internen Kurzreferenzen (**EVN vs. Wagen** nicht verwechseln, siehe `reference-evn-uic.md`). Optional: **`id`** / `articleNumber`, **`setNumber`**, **`decoderInterface`** nur bei Widerspruch zur Beschreibung oder offensichtlichem Parserfehler.
3. **Livery und Sondernamen:** Beim Splitten prüfen, ob neben Baureihe und Nummer noch **Taufname, Sonderfolierung, Piercer-/Marketing- oder Zug-/Produktname** (oft in Anführungszeichen im Roh-Import) vorkam. Wenn ja: **Finding**, falls `model.livery` noch generisch (`SBB`, `OBB`, …), `null` ist oder ein **Import-Mischstring** (z. B. halber Satz statt Lackname). Empfehlung: kurz und konkret in **`model.livery`** ablegen, Details optional im Fliesstext; nicht stillschweigend verlieren. Details: [internal/field-parsing-model.md](internal/field-parsing-model.md) («Livery nach Split»).

Ausführung in **zwei Phasen** (Pass 1, Phase 2), optional davor oder dazwischen **Auto-Fix** (siehe unten). **Standard:** keine JSON-Schreibzugriffe ohne expliziten Auto-Fix oder andere Schreibbeauftragung.

## Hard rules

1. **Scope:** Geänderte oder vom User genannte `articles/**/*.json` auf dem **aktuellen Branch** (Git wie unten), **oder** vom User genannte Pfade unter `articles/`, **oder** expliziter Scope per **Kampagnen-`tags`** (z. B. alle Dateien mit `piko-neuheiten-2024`), **oder** explizite Pfadliste. Bei Tag-Scope: alle passenden JSON unter `articles/` reviewen, nicht nur Git-Diff.
2. **Read-only:** Pass 1 und Phase 2 sind inhaltlich **Review-first**. Artikel-JSON **nur** schreiben, wenn (a) der User **Auto-Fix** ausdrücklich wünscht (siehe Abschnitt «Auto-Fix») und nur gemäss der dortigen Allowlist, oder (b) der User eine **konkrete** Änderung pro Datei oder global beauftragt (dann ausserhalb dieses Skills die üblichen Projektregeln).
3. **Ehrlichkeit:** Mehrere Lesarten klar trennen. Nicht raten ohne Kennzeichnung. **Auto-Fix** kein Raten: nur Regeln aus der Allowlist, sonst Finding und Datei unverändert lassen.

## Git: welche JSON-Dateien

Vor dem Review (Repo-Root). **Fallback** nutzen, weil viele Repos `master` statt `main` führen:

```bash
git fetch origin main 2>/dev/null || true
git fetch origin master 2>/dev/null || true
BASE=$(
  git merge-base HEAD origin/main 2>/dev/null \
  || git merge-base HEAD main 2>/dev/null \
  || git merge-base HEAD origin/master 2>/dev/null \
  || git merge-base HEAD master 2>/dev/null \
  || echo ""
)
if [ -n "$BASE" ]; then
  git diff --name-only "$BASE"...HEAD -- 'articles/**/*.json'
else
  git diff --name-only HEAD -- 'articles/**/*.json'
fi
```

- User nennt Pfade: nur diese Dateien.
- User nennt **Tag** (z. B. `piko-neuheiten-2024`): alle `articles/**/*.json` mit diesem Tag im `tags`-Array.
- Keine Diff-Dateien und kein Tag/Pfad: User fragen (gesamter `articles/`-Baum, Teilpfade oder Tag).

## Auto-Fix (optional, mechanisch)

**Auslöser:** Nur wenn der User das klar verlangt (z. B. «mit Auto-Fix», «Auto-Fix auf dem Scope», «bekannte Parserfehler automatisch»). Ohne diesen Wunsch **keinen** Auto-Fix ausführen.

**Reihenfolge:** Scope wie unter «Git» ermitteln → **Arbeitsatz erweitern** (Schwesterartikel, siehe unten) → **Auto-Fix-Pass** auf dem erweiterten Satz → **Pass 1** (Findings; bereits korrigierte Felder kurz als «Auto-Fix erledigt» markieren) → Phase 2 unverändert.

### Repo-Skripte (Python, Auto-Fix)

Alle Hilfsskripte zu diesem Skill liegen im Repo unter **`.agents/skills/lok-numbering-article-review/scripts/`** (vom **Repo-Root** aus ansprechen). Dort unter anderem:

- **`autofix_model_type_number_split.py`** — mechanischer Split `model.type` / `model.number` (Allowlist, ändert keine `description`).
- **`autofix_description_ocr.py`** — optionale OCR-/Encoding-Ersetzungen nur in **`description`**.
- **`autofill_categories_from_roco_url.py`** — wenn **`categories`** leer sind und **`source.url`** eindeutig Roco ist (`…/dampf-|diesel-|elektrolokomotiven/…`, `…/triebzuge/…`, oder `…/home-neuheiten/…` mit passendem Slug): setzt **`lokomotive`** plus passende Lok-Kategorie, bzw. **`triebwagen`** + `elektrotriebwagen` / `dieseltriebwagen` / `akkutriebwagen` (**ohne** `lokomotive`) bei Triebwagen-Slug (sonst kein Schreiben).
- **`autofill_categories_from_piko_url.py`** — analog für PIKO-Shop-URLs (gleiche Parent-Regel Triebwagen vs. Lok; **kein** Ersatz für Typ-/Nummer-Review).
- **`autofix_piko_shop_type.py`** — bereinigt PIKO-Shop-Reste in **`model.type`** (Sound-, Skalenpräfix, GTW/Re 4/4, …); Allowlist im Skript, Referenz [internal/wiki-piko-shop-parsing.md](internal/wiki-piko-shop-parsing.md).
- **`autofix_trix_shop_import.py`** — Trix- **und Märklin**-Produktdatenbank-Titel (`Dampflokomotive Baureihe …` → `BR …`; generische H1 → Typ aus Vorbild), Betriebsnummer aus Beschreibung, Livery aus Anführungszeichen, Kategorie Dampf/Diesel/Elektro, DR+DDR-Kontext `DE`→`DD`. Details: [internal/wiki-maerklin-shop-parsing.md](internal/wiki-maerklin-shop-parsing.md).
- **`autofix_ree_shop_import.py`** — REE Modèles Shop: SNCF ``BB``/``CC`` Serie vs. Laufnummer (auch wenn ``number`` noch Präfix trägt), Pacific ``231 K/G`` / ``141 D``, Moyse/040 DE/RGP-Kurztypen, Operator/Epoche/`dampflokomotive` aus Text; Referenz [reference-sncf-type-number.md](reference-sncf-type-number.md).
- **`autofix_lsmodels_shop_import.py`** — LS Models PrestaShop: langer H1 → `type`/`number`/`livery` (HLE, BB/CC, X####, AGC, Vectron, Apm/Bpm), Operator/Land aus Titel, Kategorien Triebwagen/Wagen; Referenz [internal/wiki-lsmodels-shop-parsing.md](internal/wiki-lsmodels-shop-parsing.md).
- **`autofix_model_country.py`** — setzt **`model.country`**, wenn **`null`** und der Fall zur **Skill-Allowlist** (K.P.E.V., Südbahn+AT-Kontext), zur **Operator→ISO-Map** im Skript (u. a. DB, ČSD als **CS**, VSM, GTS Rail, SBW, Balkan **CFR**→**RO**, **BDZ**→**BG**, **ŽFBH**→**BA**) oder zur **konservativen DR-Epochen-Heuristik** (``IV`` → **DD**, reine **I–III** → **DE**) passt; **Privatbahn**-Livery-Anker: [internal/wiki-privatbahn-livery-anker.md](internal/wiki-privatbahn-livery-anker.md).
- **`test_autofix_model_type_number_split.py`** — Unit-Tests zum Split-Skript.
- **`test_autofix_model_country.py`** — Unit-Tests zum Country-Skript.
- **`test_autofix_ree_shop_import.py`** — Unit-Tests zum REE-Shop-Skript.

Die folgenden Abschnitte nennen konkrete Kommandozeilen; Pfade sind immer relativ zum Repo-Root, ausser beim `cd` für `unittest`.

### Mechanischer Split (`model.type` / `model.number`)

Wenn der User **Auto-Fix** für zusammengezogene Typ-/Nummer-Felder will und der Pfad-Scope klar ist, **zuerst** das Repo-Skript **`.agents/skills/lok-numbering-article-review/scripts/autofix_model_type_number_split.py`** einsetzen (Allowlist dort codiert; **`description` wird nicht geändert**). Gleiche manuelle Regex-Arbeit nur, wenn das Skript den Fall nicht abdeckt oder der User explizit nur Einzelfälle ohne Skript will.

- **Trockenlauf (Pflicht vor Schreiben):** im Repo-Root  
  `python3 .agents/skills/lok-numbering-article-review/scripts/autofix_model_type_number_split.py <Pfad(e) oder Verzeichnis(se)>`  
  Ausgabe: eine Zeile pro betroffener Datei (Regel-Kürzel, alt → neu).
- **Schreiben:** dieselbe Zeile mit **`--apply`** (z. B. `python3 .agents/skills/lok-numbering-article-review/scripts/autofix_model_type_number_split.py --apply articles/roco`).
- **Optional:** **`--include-br`** splittet `BR 110`-artige Werte in `BR` + Ziffernblock; standardmässig **aus**, siehe Skript-Hilfe.
- **Tests:** `cd .agents/skills/lok-numbering-article-review/scripts && python3 -m unittest test_autofix_model_type_number_split -v`
- **Protokoll:** Skript-Ausgabe ins Chat übernehmen (keine stillen Massenänderungen).

**Pflichtprotokoll:** Für jede geänderte Datei eine Zeile im Chat (oder kurze Tabelle): `Pfad`, `Feld`, `alt → neu`. Keine stillen Massenänderungen.

### Schwesterartikel (Variantengruppen, herstellerneutral)

Vor dem eigentlichen Auto-Fix den **Arbeitsatz** aus dem Git-Scope wie folgt **ergänzen**:

1. **Variantengruppe definieren** über `manufacturer`, `articleNumber` / `id` und **im Projekt dokumentierte Regeln** (z. B. in [field-parsing-model.md](internal/field-parsing-model.md) oder einem `internal/wiki-*.md` zum Hersteller): welche Artikel gelten als **dieselbe Modellfamilie** (Analog/Digital/AC, Sonderlack, Set-Teil A/B)?
2. **Alle im Repo vorhandenen** JSON-Dateien derselben Gruppe unter `articles/<hersteller>/` in den Auto-Fix-Arbeitsatz aufnehmen, **auch wenn** sie nicht im Git-Diff stehen, sobald mindestens **ein** Gruppenmitglied im Scope liegt.
3. **Gleiche Korrektur nur, wenn die Allowlist-Bedingung für jede Schwester einzeln erfüllt ist** (z. B. identisches Livery-Artefakt). **Nicht** Werte von einer Variante auf eine andere **blind kopieren**, wenn sich die Ausprägung unterscheidet (z. B. **Wechselstrom vs. Gleichstrom**, andere Epoche): nur anpassen, wenn dieselbe Regel dort **eindeutig** zutrifft.
4. **Ohne dokumentierte Regel** keine automatische Scope-Erweiterung; stattdessen **Pass 1**-Finding («vermutlich Schwester von …, Regel fehlt»).

**Beispiel (nur falls im Repo weiterhin zutreffend):** Roco-Neuheiten mit siebenstelliger Nummer `73` + eine Variantenziffer + gemeinsamer vierstelliger Kern: Schwesterdateien `articles/roco/73{d}{kern}.json` mit `d ∈ {0,1,2}`. Bedeutung der Ziffer `d` und Stromsystem aus Hersteller-/Shop-Konvention ableiten, nicht global raten.

Protokoll: Schwester-Korrekturen explizit markieren (z. B. «Schwester-Variante, gleiche Gruppe wie `articles/<hersteller>/<kern>.json`»).

### Allowlist: Splitting (`model.type` / `model.number`)

Die **implementierte** mechanische Allowlist (Regex plus Dampf-Slug-Regel) liegt im Skript **`.agents/skills/lok-numbering-article-review/scripts/autofix_model_type_number_split.py`**. Bei Auto-Fix-Wunsch für Splits dieses Skript verwenden; die folgenden Bulletpoints bleiben die **inhaltliche** Referenz für Review und für Fälle **ausserhalb** des Skripts.

**Optional (nur `description`, OCR-Ersetzungen):** `.agents/skills/lok-numbering-article-review/scripts/autofix_description_ocr.py` (Dry-Run ohne `--apply`, Schreiben mit `--apply`). Kein Ersatz für inhaltliches Review.

Nur **bekannte, im Projekt oder in** [internal/field-parsing-model.md](internal/field-parsing-model.md) **dokumentierte Muster**, wenn **alle** zutreffen:

- Vollständige Betriebsnummer steht **nur** in `model.type` (z. B. Dampf-Präfix «39 1052-8», «38 2566-8»), `model.number` ist `null`, und Baureihe plus Rest sind **eindeutig** splittbar. **Beleg:** mindestens **eine** eindeutige Quelle unter `description` (sachliche erste Zeile), **`source.url`** (Pfadsegment / Slug, z. B. Roco `…-dampflokomotive-38-3713-…`) oder URL erster Zeile **ohne** Widerspruch zwischen diesen Quellen. **OCR in der Beschreibung allein** blockiert den Auto-Fix **nicht**, wenn der **URL-Slug** dieselbe Nummernaufteilung trägt.
- **Dampflok, zweistellig + vier Ziffern (ohne Prüfziffer im Titel):** `model.type` exakt im Muster **`^\d{2} \d{4}$`** (Leerzeichen genau eines), `model.number` ist `null`, `categories` enthält **`dampflokomotive`**, und `source.url` enthält die gleiche Paarung als **`{Baureihe}-{Viererblock}`** (z. B. `38-3713`, `50-1751`) → `model.type` = zweistellige Baureihe, `model.number` = Viererblock. (Häufiger Shop-/Parserrest; siehe Tabelle in `field-parsing-model.md`.)

**Nicht** Auto-Fix: **`model.electricSystem`** im Review-Skript aus Marketing-/Fliesstext oder **blind** von Schwesterdateien ableiten. **Ausnahmen:**

- **Import-Pipeline:** Parser dürfen PIKO-N-Defaults setzen (siehe [internal/field-parsing-model.md](internal/field-parsing-model.md) → «Modell-Stromsystem»).
- **REE Modèles** (`autofix_ree_shop_import.py`), nur wenn `electricSystem` **`Unbekannt`/`null`** und die Variante **artikelnummern-eindeutig** ist: SKU endet auf **`SAC`** → `AC-Digital`; endet auf **`S`** (nicht SAC) → `DC-Digital`; Basis-SKU (ohne S/SAC) **und** Titel/Beschreibung mit Analog/`DC` **oder** klarer Analog-Artikel ohne Digital-Hinweis → `DC-Analog`. Nicht aus der Schwesterdatei kopieren (Analog/S/SAC teilen oft denselben Shop-Fliesstext).

Review prüft sonst **`null`/`Unbekannt`**, Widerspruch zur Beschreibung und Schwester-Varianten. Shops nutzen oft **dieselbe** Beschreibungsbaustelle für mehrere Varianten → **Pass 1**-Finding oder **explizite** User-Anweisung. Ausserdem: jede neue Baureihe raten, SNCF/PKP-Mischfälle, **Triebzug- und Set-Artikel** ohne eindeutige Einzel-Lok-Nummer (langer `model.type`, `model.number` null, keine splittbare Betriebsnummer in URL erster Zeile — **Ausnahmen** dokumentiert in [internal/field-parsing-model.md](internal/field-parsing-model.md) → «Sets und Triebzüge»), **kein** konsistenter Nummernbeleg in `description` **und** kein passender Slug in `source.url`. Diese Fälle in **Pass 1** als Finding («Set/Serie, Schwester ggf. prüfen»), nicht raten.

### Allowlist: `model.livery`

Nur **offensichtliche Import-Artefakte** bereinigen:

- Platzhalter wie **«Info: ~»**, **«a a»**, Fragmente wie **«= Li: Oo»** → auf **`null`** setzen (oder ein Wort aus der ersten sauberen Kurzzeile der `description`, wenn dort **ein** eindeutiger Lack-/Zustandsname steht und nichts anderes passt).
- `livery` beginnt mit **Ziffer oder «4»** plus abgeschnittener deutscher Marketingphrase («4Ausführung …», «4Variante …») → **`null`** oder **eine** kurze, aus dem vollen Satz eindeutig ableitbare Bezeichnung (max. ein kurzer Begriff); wenn nicht eindeutig → **kein** Schreiben, Finding in Pass 1.
- Lange **OCR-/Fliesssätze** in `livery` (mehr als ca. 40 Zeichen oder Satzzeichen wie «—» mitten im «Lack») → auf **`null`** kürzen, **nicht** durch erfundenen Marketingtext ersetzen.
- **REE Modèles** (`autofix_ree_shop_import.py`): wenn `livery` leer, kurze Lackbezeichnung aus `description` (Anführungszeichen, `livrée …`, Farb-/Schema-Phrase wie `vert 301` / `Rouge TEE`); Depot-/Ep-/Stromsystem-Reste abschneiden, nicht raten.

### Allowlist: `model.era`

Nur wenn **eindeutig** aus `description` (erste sachliche Zeile) oder URL und **ohne** Widerspruch zu bestehendem `model.era`:

- `model.era` ist **`null`** oder offensichtlicher Tippfehler gegenüber der ersten Beschreibungszeile (z. B. «Epoche VI» vs. `null`) → auf den **kanonischen** Epochen-String aus dem Schema setzen (Projektkonvention: römische Ziffern, Kombinationen wie «III-IV» wie im Datensatz üblich).

Kein Auto-Fix, wenn Epoche im Fliesstext widersprüchlich oder nur im Marketingkörper genannt.

### Allowlist: `model.country` (sehr konservativ)

**Nur** wenn die Zuordnung **praktisch alternativlos** ist:

- `country` **`null`** und `operator` **«K.P.E.V.»** oder gleichwertig klar **Deutsches Kaiserreich** (historisch) → **`DE`**.
- `country` **`null`** und `operator` **«Südbahn»** (k. k. Südbahn) mit AT-Kontext in `description`/`categories` → **`AT`**.
- Mechanisch zusätzlich (siehe Skript): **Operator→ISO** (z. B. **DB** / **DB AG** → **DE**, **ČSD** als **CS** wie andere ČSD-Artikel, **VSM** → **NL**, **GTS Rail** → **IT**, **SBW** → **AT**, **CFR** → **RO**, **BDZ** → **BG**, **ŽFBH**/**ŽRS** → **BA**) sowie **DR**: **`IV`** in `model.era` → **DD**; reine **I / II / III** (ohne **IV**) → **DE**; **fehlende** Epoche oder andere Schreibweisen → **DD** (Default für Roco-DDR-Fälle).
- **Operator-Schreibweise:** kanonisch **`DB AG`** (Leerzeichen). Shop-Varianten **`DB-AG`** / **`DBAG`** → per Autofix/Parser auf **`DB AG`** normalisieren (nicht als eigener Operator belassen).
- **PIKO «Privatbahn»:** Livery- und Textanker → [internal/wiki-privatbahn-livery-anker.md](internal/wiki-privatbahn-livery-anker.md); nur bei eindeutigem Anker.

**Nicht** per Skript raten: Grenzverkehr ohne Anker, SNCB/SŽ-Mischungen, neue EVU-Namen ohne Eintrag in der Referenztabelle. Dort **Findings** oder Map/Skript erweitern.

**Skript:** **`.agents/skills/lok-numbering-article-review/scripts/autofix_model_country.py`** (Dry-Run ohne `--apply`). Tests: `cd` … `scripts` && `python3 -m unittest test_autofix_model_country`.

### Nach Auto-Fix

- In **Pass 1** bei betroffenen Dateien kurz vermerken: «Auto-Fix: …» (Felder), damit Phase 2 nicht dieselben Punkte erneut als offen führt, ausser der User wünscht Rücknahme.

## Phasen-Workflow (Pflicht)

### Phase 1: Erstpass über alles

- **Jede** Datei im Scope mindestens kurz anfassen (kein Überspringen im Stillen).
- Ausgabe **ein** zusammenhängendes Dokument **„Pass 1“** mit:
  - Liste aller Dateien (oder Gruppierung nur, wenn der User vorher explizit Gruppierung gleicher Muster wünscht, sonst lieber pro Datei eine Zeile Minimum).
  - Pro Datei: **klar ok** (ein Kurzsatz) **oder** **Findings** (nummeriert pro Datei: `F1`, `F2`, …) und alles **Unklare** (Parsing-Zweifel, Widersprüche, fehlende Felder).
- Keine Rückfrage an den User in Phase 1, ausser Scope unklar.
- Ende Phase 1: kurze **Statistik** (Anzahl Dateien, Anzahl mit Findings/Unklarem, häufige Muster).

#### Pass 1: PIKO-Shop (wenn Scope PIKO oder Tag PIKO-Neuheiten)

Zusätzlich zu den allgemeinen Feldern pro Datei gegen [internal/wiki-piko-shop-parsing.md](internal/wiki-piko-shop-parsing.md) prüfen:

- **`Sound-` / `inkl.`** noch in `model.type`?
- **Skalenpräfix** (`N `, …) im Typ?
- **GTW 2/6:** Livery ≠ «Stadler» wenn THURBO/HLB/StB im Titel?
- **`Rh` + `number`:** NL-Klasse, kein Split-Finding?
- **`electricSystem` null** bei N-Artikeln (PIKO ohne `Stromsystem:`-Zeile)?
- **`operator` «Privatbahn»** ohne `country` → Livery-Anker-Tabelle?
- **Parser-Artefakte** in Nebenfeldern (z. B. unrealistisches `minRadiusMm`) → Finding, kein Nummern-Split

#### Pass 1: Märklin / Trix Produktdatenbank (Tag `maerklin-*` / `trix-*`)

Gegen [internal/wiki-maerklin-shop-parsing.md](internal/wiki-maerklin-shop-parsing.md) prüfen:

- **`model.type`** nur Klassenwort (`Elektrolokomotive`, …) → Typ aus Vorbild fehlt?
- **`type`/`description` = `Suchen`** → kaputter Fetch (Suchseite), Katalog-Nachzug nötig?
- **`uvp.amount` 0** → Katalog-Preisindex nachziehen (Formate je Jahr unterschiedlich)?
- **Operator `Unbekannt`**, obwohl Vorbild `( NS )` / EVU-Name trägt?
- **`Rh`** nur bei NL/NS; ÖBB/SBB `Reihe`/`Re` nicht als Rh lassen
- Autofix zuerst: `autofix_trix_shop_import.py` (Scope `articles/maerklin` oder `articles/trix`)

#### Pass 1: LS Models (Tag `lsmodels-*` / Hersteller L.S.Models)

Gegen [internal/wiki-lsmodels-shop-parsing.md](internal/wiki-lsmodels-shop-parsing.md) prüfen:

- **Langer H1** noch in `model.type` (Komma-Marketingkette)?
- **HLE:** Nummer-first (`1312, …`) bzw. `1347 blanche … (SNCB)` → `type`/`number` gesplittet?
- **SNCF BB/CC:** Serie vs. Laufnummer ([reference-sncf-type-number.md](reference-sncf-type-number.md)); `PAYS=SNCF` nicht als `country=DE`+`Unbekannt` stehen lassen
- **X#### / AGC:** Kategorie Triebwagen (nicht nacktes `lokomotive`)?
- **Apm/Bpm/I*/M6/OCEM:** `wagen`, nicht Lok?
- **Vectron/Smartron:** kurzer `type`, Sondername in `livery`?
- Autofix zuerst: `autofix_lsmodels_shop_import.py` (Scope `articles/lsmodels`)
- **Betriebsnummer fehlt (`number` null)?** Produktbild `source.imageUrl` anschauen, siehe «Betriebsnummer aus Produktbild lesen» unten.

#### Pass 1: BEMO (Tag `bemo-*` / Hersteller BEMO)

Gegen [internal/wiki-bemo-shop-parsing.md](internal/wiki-bemo-shop-parsing.md) und [internal/wiki-rhb-mgb-schmalspur-naming.md](internal/wiki-rhb-mgb-schmalspur-naming.md) prüfen:

- **Shop-Fluff** in `model.type` (`Universallok`, `Dampflok-Fertigmodell`, `Diesellok`, …)?
- **RhB Ge 4/4 II:** Nummer in **611–633**, Taufname/Werbe in `livery`?
- **Bernina Ge 4/4 181/182:** ohne römische Generation?
- **MGB HGe 4/4 II:** Kategorie `zahnradlokomotive`?
- **StLB VL … / ZB D …:** Klassenname ganz in `type`, `number` null?
- **`source.url`:** `/produkt/…`, keine `?s=`-Suche?
- Wagen: `electricSystem` `Unbekannt`, Gattung in `type`
- **`model.era`:** aus Shop-Meta (`H0m VI`, `0m IV-V`) oder Text (`Ep. III`, `Metal Collection II`), nicht `Unbekannt` wenn Meta klar ist

### Betriebsnummer aus Produktbild lesen (herstellerneutral)

Ist `model.number` `null`, obwohl das Modell eine feste Betriebsnummer trägt (Titel nennt nur die Serie, z. B. `BB 7200`, `HLE 27`, `BR 120`, `Vectron`), steht die Nummer fast immer **auf dem Produktbild** (`source.imageUrl`, oft eine Seitenansicht oder ein Rendering). Das Bild ist eine **zulässige Beleg-Quelle**: ansehen statt raten oder auf null lassen.

1. Bild nach `.tmp/` (oder Scratchpad) laden (`curl -sL -A 'Mozilla/5.0' -o …`), mit dem Read-Tool öffnen. Nie ins Repo legen.
2. Nur Nummern übernehmen, die **klar lesbar** sind (Lokflanke, Frontnummer, UIC-Zeile). Unleserlich oder mehrdeutig → Finding, nichts schreiben.
3. Schreibweise an bestehende Artikel derselben Baureihe anpassen: SNCF/SNCB ohne Präfix und Prüfziffer (`522214` / `107284` → `22214` / `7284`), DB mit Prüfziffer (`120 144-1`, `193 366-2`), UIC-Zeile `91 80 6193 366-2 D-DB` → `193 366-2`.
4. Sondernamen und Wappen auf dem Bild (z. B. «Dole», Taufname) in `model.livery` ergänzen, kurz als Name ohne «Wappen» und ohne Farbangabe (Muster: `En Voyage, Dole`).
5. Schreiben über `articles patch`/`set-field` (nicht von Hand), danach `articles validate` bzw. `npm run check`.
6. **Schwestern** (gleiche Livery, anderes Stromsystem, z. B. DC `…07` / AC `…707`) übernehmen die Nummer nur, wenn Titel und Lackierung identisch sind. Gleiches Bild bei einem Eintrag «Variante» heisst **nicht** gleiche Nummer: dort leer lassen.
7. Triebzug/Set: Bild zeigt oft nur **einen** Wagen; Nummer gilt dann nur für diesen Wagen. Im Protokoll vermerken.

Protokoll: pro Artikel `Pfad`, `alt → neu`, Quelle «Bild».

**Bewusst nicht** Loknummer-Skill: `releaseDate`, Kampagnen-Tags, Katalog-vs.-Shop-Vollständigkeit.

### Phase 2: Datei für Datei

- **Genau eine JSON-Datei** pro Agent-Turn bearbeiten (Rückfrage-Runde), **ausser** der User verlangt ausdrücklich Selbstentscheidung («selber nachdenken», «klare Fälle selbst», «Skill anpassen»). Dann darf der Agent **eindeutige** Allowlist-/Wiki-Fälle (z. B. Privatbahn-Anker → Operator + `country`, leere `categories` → `wagen` bei Mess-/Personenwagen-Sets) **batchweise** schreiben und nur **echte** Zweifelsfälle einzeln fragen.
- Nur die **Unklarheiten und Findings** dieser Datei aus Pass 1 vorlegen (mit IDs `F1`, `F2`, …).
- **Eine** klare Frage: was soll mit welchem Punkt passieren (z. B. Split A wählen, Text später anpassen, ignorieren)?
- User-Antworten in dieser Phase:
  - **`skip`:** keine weiteren Entscheidungen zu **dieser** Datei in Phase 2; sofort **nächste** Datei mit offenen Punkten wählen. Offene Punkte dieser Datei in die **Schlussliste** als „skipped (User)“ übernehmen.
  - **`ignore`:** der User bezieht sich auf ein genanntes **Finding** (`ignore F2`) oder auf **alle** offenen Punkte dieser Datei (`ignore all`). Diese Punkte gelten für **diesen Review-Durchlauf** als **ignoriert** (nicht nacharbeiten, nicht nochmals fragen in Phase 2). In der **Schlussliste** als „ignored (this pass)“ führen.
  - Konkrete Anweisung (z. B. „Split A“, „country AT setzen“): Agent notiert als **entschieden** in der laufenden Findings-Liste. **Schreiben** in die JSON nur, wenn der User danach explizit editieren lässt, Auto-Fix/Änderungslauf dafür schon beauftragt ist, **oder** Selbstentscheidung wie oben gilt und die Regel dokumentiert ist.
- Neue wiederkehrende Anker: Wiki/Skript erweitern, dann patchen (nicht nur einmalig hartcodieren).
- Nach jeder User-Antwort: entweder nächstes Finding derselben Datei fragen oder nächste Datei, bis keine Datei mehr mit **nicht** `skip`/`ignore` behandelten offenen Punkten übrig ist (oder User Session beendet).

### Datei in der Antwort (Pflicht, Phase 2)

- Sobald eine **konkrete** `articles/**/*.json` in Phase 2 **im Fokus** steht: in **derselben** Antwort **immer** den **vollen Repo-relativen Pfad** nennen (eine Zeile, z. B. `articles/roco/70078.json` oder `articles/<hersteller>/….json`). **Kein** vollständiger Dateiinhalt in der Antwort, ausser der User verlangt ausdrücklich den Inhalt oder einen Ausschnitt.
- Pass 1: keine Pflicht, alle Pfade einzeln aufzuzählen; bei Phase 2 pro Fokusdatei der Pfad reicht.

### Ignorierte und erneuter Review

- Findings oder Dateien, die in Phase 2 als **`ignore`** markiert wurden, **nicht** von alleine in einem späteren Turn derselben Session wieder aufrollen.
- **Erneutes** Prüfen zuvor ignorierten Inhalts nur, wenn der User **explizit** verlangt (z. B. „zweiter Pass, diesmal inklusive ignorierte“ oder namentlich Dateien nennen).

## Domain-Wissen (progressive disclosure)

| Thema | Datei |
|--------|--------|
| Repo-Skripte (Split, OCR, Tests) | Ordner `.agents/skills/lok-numbering-article-review/scripts/` (siehe Abschnitt «Repo-Skripte» unter Auto-Fix) |
| Splitting `model.type` / `model.number` | [internal/field-parsing-model.md](internal/field-parsing-model.md) |
| Modell-`electricSystem` (DC/AC am Modell) | [internal/field-parsing-model.md](internal/field-parsing-model.md) («Modell-Stromsystem») |
| PIKO Shop-Titel / Import-Artefakte | [internal/wiki-piko-shop-parsing.md](internal/wiki-piko-shop-parsing.md) |
| Märklin / Trix Produktdatenbank | [internal/wiki-maerklin-shop-parsing.md](internal/wiki-maerklin-shop-parsing.md) |
| BEMO Shop / Katalog-Artefakte | [internal/wiki-bemo-shop-parsing.md](internal/wiki-bemo-shop-parsing.md) |
| LS Models Shop (lsmodels.eu) | [internal/wiki-lsmodels-shop-parsing.md](internal/wiki-lsmodels-shop-parsing.md) |
| Shop-Import-Workflow (PDF → Queue → Fetch → Pipeline) | Skill [locobox-import](../locobox-import/SKILL.md), CLI [`tools/cli`](../../../tools/cli/README.md) |
| Privatbahn → Land (Livery-Anker) | [internal/wiki-privatbahn-livery-anker.md](internal/wiki-privatbahn-livery-anker.md) |
| Baureihen-/UIC-Schemata (Link-Index) | [internal/wiki-baureihen-schemata-uebersicht.md](internal/wiki-baureihen-schemata-uebersicht.md) |
| EVN / 12 Stellen | [internal/wiki-eindeutige-fahrzeugnummer.md](internal/wiki-eindeutige-fahrzeugnummer.md) |
| UIC-Wagennummer, Luhn | [internal/wiki-uic-wagennummer.md](internal/wiki-uic-wagennummer.md) |
| CH Bauartbezeichnungen | [internal/wiki-schweizer-bauartbezeichnungen.md](internal/wiki-schweizer-bauartbezeichnungen.md) |
| RhB / MGB / Schmalspur-Naming (Ge/HGe, Wagen, StLB/ZB, DR 99) | [internal/wiki-rhb-mgb-schmalspur-naming.md](internal/wiki-rhb-mgb-schmalspur-naming.md) |
| ÖBB Überblick | [internal/wiki-oebb-loks-liste.md](internal/wiki-oebb-loks-liste.md) |
| DB Baureihen | [internal/wiki-db-baureihen-liste.md](internal/wiki-db-baureihen-liste.md) |
| DR 1920–1945 (Reichsbahn) | [internal/wiki-dr-reichsbahn-1920-1945-baureihen-liste.md](internal/wiki-dr-reichsbahn-1920-1945-baureihen-liste.md) |
| DDR: DR-Baureihen (1945–1993) | [internal/wiki-dr-ddr-baureihen-liste.md](internal/wiki-dr-ddr-baureihen-liste.md) |
| SNCF Überblick (Frankreich) | [internal/wiki-sncf-loks-liste.md](internal/wiki-sncf-loks-liste.md) |
| SNCF `type` / `number` (BB/CC Serie vs. Laufnummer) | [reference-sncf-type-number.md](reference-sncf-type-number.md) |
| Jouef Katalog (HJ#### / S, Mehrspalten-PDF) | [internal/wiki-jouef-catalog-parsing.md](internal/wiki-jouef-catalog-parsing.md) |
| Italien Überblick | [internal/wiki-italien-loks-liste.md](internal/wiki-italien-loks-liste.md) |
| Niederlande Überblick | [internal/wiki-niederlande-loks-liste.md](internal/wiki-niederlande-loks-liste.md) |
| Ungarn | [internal/wiki-ungarn-loks-liste.md](internal/wiki-ungarn-loks-liste.md) |
| Rumänien (CFR / Privat) | [internal/wiki-rumaenien-loks-liste.md](internal/wiki-rumaenien-loks-liste.md) |
| Bulgarien (BDZ / Privat) | [internal/wiki-bulgarien-loks-liste.md](internal/wiki-bulgarien-loks-liste.md) |
| Bosnien und Herzegowina (ŽFBH / ŽRS) | [internal/wiki-bosnien-herzegowina-loks-liste.md](internal/wiki-bosnien-herzegowina-loks-liste.md) |
| Amintiri Feroviare / AF Models Shop | [internal/wiki-amintiri-feroviare-shop-parsing.md](internal/wiki-amintiri-feroviare-shop-parsing.md) |
| Slowenien (nur Dampf) | [internal/wiki-slowenien-dampf-loks-liste.md](internal/wiki-slowenien-dampf-loks-liste.md) |
| Slowakei (ŽSSK) | [internal/wiki-slowakei-zssk-loks-liste.md](internal/wiki-slowakei-zssk-loks-liste.md) |
| Tschechien / ČD / ČSD (Lokklassen; ggf. Bezug SI) | [internal/wiki-tschechien-lokklassen-liste.md](internal/wiki-tschechien-lokklassen-liste.md) |
| Polen PKP | [internal/wiki-polen-pkp-loks-liste.md](internal/wiki-polen-pkp-loks-liste.md) |
| Schweden | [internal/wiki-schweden-loks-kategorien.md](internal/wiki-schweden-loks-kategorien.md) |
| Norwegen | [internal/wiki-norwegen-loks-kategorien.md](internal/wiki-norwegen-loks-kategorien.md) |
| Dänemark DSB | [internal/wiki-daenemark-dsb-loks-liste.md](internal/wiki-daenemark-dsb-loks-liste.md) |
| Luxemburg | [internal/wiki-luxemburg-loks-kategorien.md](internal/wiki-luxemburg-loks-kategorien.md) |
| Belgien (NMBS/SNCB) | [internal/wiki-belgien-nmbs-loks-liste.md](internal/wiki-belgien-nmbs-loks-liste.md) |
| Ordner / Erweiterung | [internal/README.md](internal/README.md) |
| EVN vs Wagen | [reference-evn-uic.md](reference-evn-uic.md) |
| Locobox-Felder | [reference-triebfahrzeug-formate.md](reference-triebfahrzeug-formate.md) |

Vor dem Review: `contracts/article.schema.json` kurz ansehen.

**`internal/wiki-*.md`:** Inhalt ist **komprimiertes Validierungswissen** (Länder, Operatoren, Stromsysteme, typische Baureihen, Kategoriechecks). **Ausnahme:** [wiki-baureihen-schemata-uebersicht.md](internal/wiki-baureihen-schemata-uebersicht.md) ist absichtlich ein **Link-Index**; einige Länderdateien haben ausserdem **einen** Primärlink unter dem Titel (deutsche Wikipedia als Korrektur). Sonst: keine langen Linklisten im Fliesstext; Herkunft weiterhin unter **«Provenienz»** je Datei.

## Inhalt pro Datei (Pass 1 und als Referenz in Phase 2)

Pro Datei mindestens:

- **Roh:** `model.type`, `model.number`, **`model.livery`**, `model.electricSystem`, `model.scale`, `model.era`, `categories` (wenn für den Fehler relevant)
- **Parsing / Split:** sicher / wahrscheinlich / unklar, ggf. Vorschlag A/B
- **Plausibilität:** ok / unklar / widersprüchlich, Stichpunkte (inkl. **Livery vs Sondername** aus Roh-`type` oder Beschreibung; **Stromsystem** vs. Text und vs. **Schwester-Variante** derselben dokumentierten Modellfamilie; **Kategorie** vs. Antrieb; **Triebzug/Set** mit `number` null und langem `type` ohne EVN-Split; **`description`** / **`source.url`** bei OCR-Müll oder deutschsprachigem Fliesstext vs. ausländischem Vorbild)
- **Findings** mit IDs `F1`, `F2`, … für Phase 2

## Schlussliste (Ende Phase 2 oder bei Abbruch)

Ein Abschnitt **„Findings-Übersicht“**:

- **Auto-Fix** (falls gelaufen): kurze Liste `Pfad` + geänderte Felder (kann mit «Erledigt» überlappen).
- **Erledigt / entschieden** (kurz, mit Dateipfad und Finding-ID).
- **Offen** (skipped ohne Resolution).
- **Ignored (this pass)** (Pfad + ID oder „whole file“).

Sprache: Deutsch, **Schweizer Rechtschreibung** (Umlaute, kein Eszett).
