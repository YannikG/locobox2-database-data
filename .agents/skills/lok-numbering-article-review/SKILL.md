---
name: lok-numbering-article-review
description: >-
  Two-phase Locobox article JSON review: (1) full pass listing all findings and
  unclear items per file, (2) one file at a time user resolves unclear items
  (skip / ignore). Parsing model.type vs model.number and plausibility. Read-only
  until user orders edits. Re-review of ignored items only when user explicitly
  asks. Use for Loknummer review or when this skill is attached.
disable-model-invocation: true
---

# Loknummerierung: Parsing, Split, Plausibilität (zwei Phasen)

## Hauptziel

1. **Parsen und splitten:** Aus `model.type` (und bei Bedarf `description`, `source.url`, `model.number`) Baureihe/Reihe vs laufende Nummer ableiten.
2. **Plausibilität:** Abgleich mit Operator, Land, Kategorien, Fliesstext, internen Kurzreferenzen (EVN vs Wagen nicht verwechseln).
3. **Livery und Sondernamen:** Beim Splitten prüfen, ob neben Baureihe und Nummer noch **Taufname, Sonderfolierung, Piercer-/Marketing- oder Zug-/Produktname** (oft in Anführungszeichen im Roh-Import) vorkam. Wenn ja: **Finding**, falls `model.livery` noch generisch (`SBB`, `OBB`, …), `null` ist oder ein **Import-Mischstring** (z. B. halber Satz statt Lackname). Empfehlung: kurz und konkret in **`model.livery`** ablegen, Details optional im Fliesstext; nicht stillschweigend verlieren. Details: [internal/field-parsing-model.md](internal/field-parsing-model.md) («Livery nach Split»).

Ausführung immer in **zwei Phasen** (siehe unten). Keine automatischen JSON-Schreibzugriffe.

## Hard rules

1. **Scope:** Nur geänderte oder vom User genannte `articles/**/*.json` auf dem **aktuellen Branch** (Git wie unten), oder nur genannte Pfade unter `articles/`.
2. **Read-only:** In beiden Phasen keine Artikel-JSON schreiben, ausser der User beauftragt explizit danach eine Änderung.
3. **Ehrlichkeit:** Mehrere Lesarten klar trennen. Nicht raten ohne Kennzeichnung.

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
- Keine Diff-Dateien: User fragen (gesamter `articles/`-Baum oder Teilpfade).

## Phasen-Workflow (Pflicht)

### Phase 1: Erstpass über alles

- **Jede** Datei im Scope mindestens kurz anfassen (kein Überspringen im Stillen).
- Ausgabe **ein** zusammenhängendes Dokument **„Pass 1“** mit:
  - Liste aller Dateien (oder Gruppierung nur, wenn der User vorher explizit Gruppierung gleicher Muster wünscht, sonst lieber pro Datei eine Zeile Minimum).
  - Pro Datei: **klar ok** (ein Kurzsatz) **oder** **Findings** (nummeriert pro Datei: `F1`, `F2`, …) und alles **Unklare** (Parsing-Zweifel, Widersprüche, fehlende Felder).
- Keine Rückfrage an den User in Phase 1, ausser Scope unklar.
- Ende Phase 1: kurze **Statistik** (Anzahl Dateien, Anzahl mit Findings/Unklarem, häufige Muster).

### Phase 2: Datei für Datei

- **Genau eine JSON-Datei** pro Agent-Turn bearbeiten (Rückfrage-Runde).
- Nur die **Unklarheiten und Findings** dieser Datei aus Pass 1 vorlegen (mit IDs `F1`, `F2`, …).
- **Eine** klare Frage: was soll mit welchem Punkt passieren (z. B. Split A wählen, Text später anpassen, ignorieren)?
- User-Antworten in dieser Phase:
  - **`skip`:** keine weiteren Entscheidungen zu **dieser** Datei in Phase 2; sofort **nächste** Datei mit offenen Punkten wählen. Offene Punkte dieser Datei in die **Schlussliste** als „skipped (User)“ übernehmen.
  - **`ignore`:** der User bezieht sich auf ein genanntes **Finding** (`ignore F2`) oder auf **alle** offenen Punkte dieser Datei (`ignore all`). Diese Punkte gelten für **diesen Review-Durchlauf** als **ignoriert** (nicht nacharbeiten, nicht nochmals fragen in Phase 2). In der **Schlussliste** als „ignored (this pass)“ führen.
  - Konkrete Anweisung (z. B. „Split A“, „country AT setzen“): Agent notiert als **entschieden** in der laufenden Findings-Liste (weiterhin read-only bis der User separat editieren lässt).
- Nach jeder User-Antwort: entweder nächstes Finding derselben Datei fragen oder nächste Datei, bis keine Datei mehr mit **nicht** `skip`/`ignore` behandelten offenen Punkten übrig ist (oder User Session beendet).

### Datei in der Antwort (Pflicht, Phase 2)

- Sobald eine **konkrete** `articles/**/*.json` in Phase 2 **im Fokus** steht: in **derselben** Antwort **immer** den **vollen Repo-relativen Pfad** nennen (eine Zeile, z. B. `articles/roco/70078.json`). **Kein** vollständiger Dateiinhalt in der Antwort, ausser der User verlangt ausdrücklich den Inhalt oder einen Ausschnitt.
- Pass 1: keine Pflicht, alle Pfade einzeln aufzuzählen; bei Phase 2 pro Fokusdatei der Pfad reicht.

### Ignorierte und erneuter Review

- Findings oder Dateien, die in Phase 2 als **`ignore`** markiert wurden, **nicht** von alleine in einem späteren Turn derselben Session wieder aufrollen.
- **Erneutes** Prüfen zuvor ignorierten Inhalts nur, wenn der User **explizit** verlangt (z. B. „zweiter Pass, diesmal inklusive ignorierte“ oder namentlich Dateien nennen).

## Domain-Wissen (progressive disclosure)

| Thema | Datei |
|--------|--------|
| Splitting `model.type` / `model.number` | [internal/field-parsing-model.md](internal/field-parsing-model.md) |
| EVN / 12 Stellen | [internal/wiki-eindeutige-fahrzeugnummer.md](internal/wiki-eindeutige-fahrzeugnummer.md) |
| UIC-Wagennummer, Luhn | [internal/wiki-uic-wagennummer.md](internal/wiki-uic-wagennummer.md) |
| CH Bauartbezeichnungen | [internal/wiki-schweizer-bauartbezeichnungen.md](internal/wiki-schweizer-bauartbezeichnungen.md) |
| ÖBB Überblick | [internal/wiki-oebb-loks-liste.md](internal/wiki-oebb-loks-liste.md) |
| DB Baureihen | [internal/wiki-db-baureihen-liste.md](internal/wiki-db-baureihen-liste.md) |
| SNCF Überblick (Frankreich) | [internal/wiki-sncf-loks-liste.md](internal/wiki-sncf-loks-liste.md) |
| Italien Überblick | [internal/wiki-italien-loks-liste.md](internal/wiki-italien-loks-liste.md) |
| Niederlande Überblick | [internal/wiki-niederlande-loks-liste.md](internal/wiki-niederlande-loks-liste.md) |
| Ungarn | [internal/wiki-ungarn-loks-liste.md](internal/wiki-ungarn-loks-liste.md) |
| Rumänien | [internal/wiki-rumaenien-loks-liste.md](internal/wiki-rumaenien-loks-liste.md) |
| Slowenien (nur Dampf) | [internal/wiki-slowenien-dampf-loks-liste.md](internal/wiki-slowenien-dampf-loks-liste.md) |
| Tschechien (Lokklassen; ggf. Bezug SI) | [internal/wiki-tschechien-lokklassen-liste.md](internal/wiki-tschechien-lokklassen-liste.md) |
| Polen PKP | [internal/wiki-polen-pkp-loks-liste.md](internal/wiki-polen-pkp-loks-liste.md) |
| Schweden | [internal/wiki-schweden-loks-kategorien.md](internal/wiki-schweden-loks-kategorien.md) |
| Norwegen | [internal/wiki-norwegen-loks-kategorien.md](internal/wiki-norwegen-loks-kategorien.md) |
| Dänemark DSB | [internal/wiki-daenemark-dsb-loks-liste.md](internal/wiki-daenemark-dsb-loks-liste.md) |
| Luxemburg | [internal/wiki-luxemburg-loks-kategorien.md](internal/wiki-luxemburg-loks-kategorien.md) |
| Ordner / Erweiterung | [internal/README.md](internal/README.md) |
| EVN vs Wagen | [reference-evn-uic.md](reference-evn-uic.md) |
| Locobox-Felder | [reference-triebfahrzeug-formate.md](reference-triebfahrzeug-formate.md) |

Vor dem Review: `contracts/article.schema.json` kurz ansehen.

**`internal/wiki-*.md`:** Inhalt ist **komprimiertes Validierungswissen** (Länder, Operatoren, Stromsysteme, typische Baureihen, Kategoriechecks). **Keine** Wikipedia-Linklisten im Hauptteil; Herkunft nur unten in der jeweiligen Datei unter **«Provenienz»** (ein Absatz, kein Pflicht-Klick).

## Inhalt pro Datei (Pass 1 und als Referenz in Phase 2)

Pro Datei mindestens:

- **Roh:** `model.type`, `model.number`, **`model.livery`** (wenn vom Split oder vom Import her relevant)
- **Parsing / Split:** sicher / wahrscheinlich / unklar, ggf. Vorschlag A/B
- **Plausibilität:** ok / unklar / widersprüchlich, Stichpunkte (inkl. **Livery vs Sondername** aus Roh-`type` oder Beschreibung)
- **Findings** mit IDs `F1`, `F2`, … für Phase 2

## Schlussliste (Ende Phase 2 oder bei Abbruch)

Ein Abschnitt **„Findings-Übersicht“**:

- **Erledigt / entschieden** (kurz, mit Dateipfad und Finding-ID).
- **Offen** (skipped ohne Resolution).
- **Ignored (this pass)** (Pfad + ID oder „whole file“).

Sprache: Deutsch, **Schweizer Rechtschreibung** (Umlaute, kein Eszett).
