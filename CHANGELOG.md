# Changelog

## Statistical analysis checkpoint — 2026-10-08

- Historical buyer/seller VaR and fractional-tail Expected Shortfall at 95%/99%, observed-step horizons, stress paths and signed benchmark-budget scenarios, with minimum tail coverage.
- Completed-year monthly-change summaries, fixed early/late splits, leave-one-year-out sensitivity and reproducible joint two-year block-bootstrap intervals when coverage is sufficient.
- Exact original-interval commodity/FX log-change variance decomposition, retaining negative contributions and explicitly undefined shares.
- Leakage-free walk-forward MAE/RMSE and naive-baseline skill comparisons for last price, expanding-history drift and trailing-20 mean.
- Independent stocks-to-use panel with release vintages, invented examples and staged private normalized CSV import. Five panels calculate lazily and do not transmit or persist imported data.

## Expanded market analysis checkpoint — 2026-10-08

- Add dated market snapshots, one/five-year empirical price positions, exact-date commodity/FX/interaction attribution, common-date index100 comparisons, Wilder RSI14, unannualized20/60-observation log-change volatility, exact-interval return correlations, wheat/corn benchmark spreads, equal-year seasonal quartiles and explicit benchmark scenarios.
- Add browser-only CSV processing without data-upload requests or persistent browser storage. Keep user-file identities separate from invented samples; retain the local SQLite import workflow and full-precision CSV export.
- Document methods, reference dates, warmup, gaps, futures continuation limits and private user-data handling. Include all inline browser assets in installed packages.

## Unreleased — 2026-10-07

- Current-inclusive five-calendar-year monthly price comparison with equal-year period mean and observed coverage.
- Six-line technical plot: price, SMA20/100/200 and Bollinger20 upper/lower (±2 population standard deviations), full-history warm-up, exact 12-calendar-month default range and matching CSV export.

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
- Added a ten-year month-row price matrix comparing monthly means with a dated, cutoff-visible daily reference, with explicit color meanings, missing cells and partial-month markers.
- Renamed the price matrix Monthly average prices, displayed its monthly prices without decimal places and replaced unavailable numeric table values with —, distinguishing future months from historical gaps.
- Price-matrix display precision now depends on units: whole commodity prices and three decimals for currency quotes, including the corresponding reference value.
- Prepared a synthetic-only GitHub Pages explorer with mobile table/chart scrolling, collapsed advanced analysis, local-app guidance, reproducible builder and sample CSV. Hosting activation remains separate from committing the page.
- Expanded the public synthetic explorer to wheat, corn, rapeseed and EUR/PLN, EUR/USD, derived USD/PLN; all three commodities support exact-date synthetic PLN/t views.

### Private XLSX import and usability

- Added local Excel master-file preview, sheet/row/column mapping, explicit role/unit selection, strict validation and a separate atomic Add step.
- Added same-workbook positive exact-date PLN views, currency attribution/scenarios and declared wheat/corn spreads without joining invented sample FX.
- Added accessible section navigation, indicator explanations, warmup messages, mobile overflow/touch improvements and privacy-preserving view settings with reset.
- Bundled pinned SheetJS CE0.20.3 mini reader and its Apache-2.0 license, with no runtime CDN requests.
