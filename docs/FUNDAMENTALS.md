# Fundamental context: normalized publication vintages

SeasonLens accepts a private **normalized CSV** and includes an explicitly
invented example. It does not download official balances or authenticate a
provider claim. Uploaded fundamental data remain independent of price series:
select a commodity and geography explicitly. A wheat balance for an entire
country or the world is context, not the deliverable supply balance for a
particular futures contract.

## File format

Use UTF-8, comma delimiters, and exactly this header in this order:

```csv
publication_date,commodity,region,marketing_year,unit,ending_stocks,total_use
```

| Field | Definition and validation |
| --- | --- |
| `publication_date` | Actual release date, `YYYY-MM-DD`; not observation date, download date or marketing-year end. |
| `commodity` | Exactly `wheat`, `corn`, or `rapeseed`. Aggregate oilseeds or coarse grains are not substitutes. |
| `region` | Explicit case-sensitive geography, trimmed text of 1–80 characters. |
| `marketing_year` | Consecutive year label, e.g. `2025/26`. |
| `unit` | One of `metric tonnes`, `thousand metric tonnes`, `million metric tonnes`, `bushels`, `thousand bushels`, `million bushels`. Both quantities use this same unit. |
| `ending_stocks` | Finite real quantity, at least zero. |
| `total_use` | Finite real quantity, greater than zero, with the same commodity/geographic/marketing-year scope as stocks. |

Numbers use decimal points, without thousands separators, blanks or missing
markers. Scientific notation is accepted. Nonzero magnitudes must be between
`1e-100` and `1e100`. Files are limited to 12 MiB and 20,000 data rows.
Quoted fields and doubled quotes are supported; embedded control characters in
labels are rejected. A UTF-8 BOM is permitted. Extra provider/source fields,
ambiguous headers, raw official layouts, duplicate vintage keys and changing
quantity units within one commodity/geography/marketing year are rejected.
Normalize units explicitly outside this importer; it does not guess conversions.

An invented, download-ready example is
[`synthetic_fundamentals.csv`](../examples/data/synthetic_fundamentals.csv).
Its release dates and all quantities are fictional and are not USDA estimates.
Private imports are labelled `USER_FILE`; built-in demonstration data are
labelled `SYNTHETIC`. A manually entered label cannot turn private data into a
verified official source.

## Calculation and release timing

Stock-to-use (%) = `100 × ending_stocks / total_use`.
For example, invented stocks of 25 and use of 100 give **25%**. A later release
revising stocks to 24 and use to 102 gives **23.5294117647%**, a revision of
**−1.4705882353 percentage points**. Quantity revisions are −1 and +2 in the
explicitly declared unit. Percentages and percentage-point changes are different
measures.

All original rows are validated before applying the analysis cutoff, including
invalid or duplicate future releases. Among valid rows, only releases on or
before the explicit cutoff are eligible. The latest and previous releases are
selected within the chosen commodity, geography and marketing year. Default
marketing year is the greatest **cutoff-visible** year for the selected pair;
you can select a specific year. No later revision is substituted into an earlier
cutoff, no geographic aggregation occurs, and missing releases remain missing.
A new marketing year starts a new revision sequence.

A low ratio is a descriptive measure of inventories relative to use. It does
not independently predict price, establish causation, or account for inventory
accessibility, quality, exports, delivery specifications or reporting changes.
Do not compare unlike regions, quantities or marketing-year definitions. The
module intentionally does not regress a continuation price on unreconciled
balance data or promise an automatic fundamental feed.

## Preparing actual data

USDA publishes monthly WASDE reports and historical releases at the
[official WASDE page](https://www.usda.gov/about-usda/general-information/staff-offices/office-chief-economist/commodity-markets/wasde-report).
To prepare a private normalized import, choose the exact commodity and balance,
retain the report's publication date and marketing year, and supply ending
stocks and consistently defined total use in one declared unit. Verify these
fields against each original release. Do not backdate the latest revised table
as if it had been known earlier. Generic oilseed totals are not rapeseed data.
Other providers require the same normalization and applicable usage rights.
There is currently **no tested raw-WASDE adapter or automatic collection job**.

## Pure JavaScript API

`SeasonLensFundamentals` in the browser, or `require('./fundamentals.js')`:

- `parseCSV(text)` validates the complete CSV and returns a sorted independent
  array of normalized records.
- `validateRows(rows)` applies the same complete-record validation without CSV
  parsing and returns an independent array.
- `analyze(rows, {asOf, commodity, region, marketingYear?, source?})` validates all
  rows, applies the inclusive cutoff, and returns `available`, `reason`,
  `selection`, `source`, `counts`, `marketing_years`, `latest`, `previous` and
  `revisions`. Source defaults to `USER_FILE`; only `USER_FILE` and `SYNTHETIC`
  are accepted. Each revision includes release fields, `stocks_to_use_percent`,
  `previous_publication_date`, `ending_stocks_change`, `total_use_change` and
  `stocks_to_use_change_pp`. Unavailable revisions are `null`, not zero.
- `demoRows()` returns fresh invented records, never official observations.

The API never reads the clock, performs network requests, persists data,
mutates input, fills observations, or automatically joins a price series.
