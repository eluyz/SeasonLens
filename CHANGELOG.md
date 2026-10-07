# Changelog

## Unreleased — 2026-10-07

- Private SQLite persistence with atomic updates, revision audit, source/quote isolation, export and backups.
- Direct ECB reference-rate parser/updater and same-date derived USD/PLN; reserved IDs protected from CSV imports.
- Local CSV import app and multi-instrument standalone explorer with SMA20/50, line/range controls, monthly-change heatmap, matched partial-month comparisons, normalized profiles/base dates, exact-date PLN conversion and coverage.
- Entirely invented explorer example and inactive private nightly runner template. Automatic MATIF continuation-close collection and a hosted job remain unimplemented.

- Auto-scaled shared chart axes with padding, readable narrow-range labels and an embedded visual legend for lines, historical range and partial months.

- Equal-year seasonal profiles for exact declared calendar windows with coverage and monthly-mean extrema.
- Explicit inclusive reference date, current-year comparison and visible partial-calendar-month status.
- Standalone local HTML/SVG charts and inspectable tables; synthetic CSV-to-report example.

- Read-only quality reports for prepared daily series, including source-row mappings.
- Explicit local CSV import with instrument selection, auditable blank-value omissions and date cutoffs.
- Synthetic CSV-to-monthly command-line example; at that earlier checkpoint no graphical file selector, XLSX reader or external data feed existed.

## 0.0.1 — Experimental checkpoint, 2026-10-07

- Initial project configuration and monthly aggregation contract.
- Monthly means/counts implementation, synthetic example and nine acceptance tests.
- Explicit errors for aggregation overflow and unsupported wider floating-point types.
- Initial import into the public repository with English documentation; no release tag yet. See STATUS.md for completed validation.
