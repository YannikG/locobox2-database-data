# Roco Catalog + UVP Scraper

Use this skill when user asks to extract, merge, or generate Roco article data from:
- Roco novelty catalog PDF
- Roco UVP price list PDF

## Goal

Create validated article JSON files in `articles/roco/` by combining catalog facts with UVP prices.

## Required Inputs

- `catalogPdf`: full Roco catalog PDF
- `pricePdf`: Roco UVP price list PDF
- `year`: target year, for reporting

## Process

1. Parse UVP list first.
   - Extract table rows: article number, catalog page, UVP.
   - Normalize price from comma decimal (`269,90`) to float (`269.9`).
2. Parse catalog second.
   - Find product blocks by article number and nearby metadata.
   - Extract only clearly visible facts.
3. Merge strict by `articleNumber`.
   - UVP always comes from price list.
   - Catalog details come from catalog pages.
4. Generate one file per article:
   - `articles/roco/{articleNumber}.json`
5. Write unmatched UVP rows to:
   - `imports/roco/unmatched-uvp-{year}.csv`

## Mapping Rules

- `id`: `roco-{articleNumber}`
- `manufacturer`: `Roco`
- `uvp.currency`: `EUR`
- `releaseDate`: ISO date `YYYY-MM-DD`
- `updatedAt`: ISO UTC timestamp
- `model.luepMm` and `model.minRadiusMm` in millimeters
- Unknown fields: set `null`, never invent values

## Validation Checklist

- No duplicate article numbers
- Every generated JSON parseable
- `uvp.amount` is numeric and > 0
- `source` contains catalog and UVP references
- Unmatched rows documented

## Agent Output Format

When task ends, report:
- number of generated article files
- number of unmatched UVP rows
- list of articles with uncertain or missing required fields

## Prompt Starter

```text
Extract and merge Roco article data from:
- catalogPdf: <path>
- pricePdf: <path>
- year: <year>

Rules:
1) Parse UVP table first (Art. Nr., Seite, UVP EUR).
2) Parse catalog pages and enrich article facts.
3) Merge strictly by articleNumber.
4) Generate one JSON per article in articles/roco/.
5) Do not invent facts; use null when uncertain.
6) Export unmatched UVP rows to imports/roco/unmatched-uvp-{year}.csv.
7) Return counts and open data-quality risks.
```
