# ACME Catalog Scraper

Use this skill when user asks to extract ACME article data from one or more ACME catalog PDFs.

## Goal

Create validated article JSON files in `articles/acme/` from ACME catalog content.

## Required Inputs

- `catalogPdf`: ACME catalog PDF path
- `year`: catalog year, for reporting

Optional:
- `pricePdf`: ACME price list PDF, if available
- `defaultCurrency`: default `EUR`
- `defaultReleaseDate`: fallback ISO date

## Process

1. Parse symbol legend first.
   - Build mapping for icon meaning, especially:
     - scale
     - minimum radius
     - length over buffers
     - DC/AC system
     - decoder interface
     - sound or digital readiness
     - epoch labels
2. Parse catalog pages.
   - Detect product blocks with article number and product title.
   - Extract only explicit facts from nearby text and symbols.
   - Support variant blocks with multiple article numbers.
3. Parse prices.
   - If `pricePdf` exists, use it as primary price source.
   - If no `pricePdf`, use only explicit catalog prices.
4. Merge by `articleNumber`.
   - One output JSON per article number.
5. Write unmatched records:
   - `imports/acme/unmatched-{year}.csv`

## Mapping Rules

- `id`: `acme-{articleNumber}`
- `manufacturer`: `Acme`
- `articleNumber`: string, no spaces
- `uvp.amount`: decimal number
- `uvp.currency`: uppercase ISO code, default `EUR`
- `releaseDate`: `YYYY-MM-DD`
- `updatedAt`: ISO UTC datetime
- `model.minRadiusMm`: integer mm
- `model.luepMm`: integer mm
- Unknown fields: `null`, never guessed

## Data Quality Rules

- No duplicate article numbers
- All generated JSON files parse correctly
- Required fields from article schema present
- If price missing, keep record but flag in unmatched report
- Add source trace for each article:
  - PDF file reference
  - page number
  - short extraction notes

## Agent Output Format

When task ends, report:
- count of generated article files
- count of unmatched or partial records
- list of records missing required business fields
- assumptions made during extraction

## Prompt Starter

```text
Extract ACME catalog data from:
- catalogPdf: <path>
- year: <year>
- optional pricePdf: <path>

Rules:
1) Parse symbol legend first and map icon semantics.
2) Extract product blocks and article numbers page by page.
3) Merge records strictly by articleNumber.
4) Generate one JSON per article under articles/acme/.
5) Use only explicit facts from document; unknown = null.
6) Export unmatched or partial records to imports/acme/unmatched-{year}.csv.
7) Return counts, open risks, and extraction assumptions.
```
