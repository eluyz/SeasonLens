# Decisions

## 2026-10-07 — First checkpoint

- Scope: monthly arithmetic means and observation counts only. Importers, multi-year profiles and UI are separate tasks.
- Use prepared datetime/numeric columns to keep parsing out of the mathematical core.
- Retain all intervening years and all 12 months so missing data stay visible.
- Use pandas 2.2.3, available in the development environment, and pin it for this experimental checkpoint.
- Use standard-library unittest for the first independent acceptance cases because pytest is not available in the current environment. This revises the plan's proposed testing tool, not its mathematical acceptance criteria.
- Research of existing tools and confirmation of the product's value remain necessary before expanding toward a public application.
- The first checkpoint was stored as an archive before repository setup. The owner has now connected the public repository eluyz/SeasonLens. Source files will be maintained there; no release tag or background runner is configured.
- Independent review exposed numeric overflow and unsupported long-double inputs. Reject these explicitly; do not silently emit infinite means or expose pandas' internal type error.
- Use English for all repository documentation, code comments, issue text and commit messages. Coordination with the owner continues in Polish.

## 2026-10-07 — Public code and private market data

- Keep raw imported futures prices, private provenance and restricted derived outputs private. Public documentation does not identify the owner's private data provider. Private storage does not extend usage rights.
- Continue with synthetic public examples and a local file-import workflow. Source-specific terms are separate from the MIT code license.
- Select direct ECB daily reference rates for future public FX examples, with attribution and clearly marked calculations.
- Treat direct Euronext Delayed Trade Data as a separate conditional candidate for new sessions. Its terms do not clear an existing vendor-sourced MATIF history or establish a free long historical archive.
- Record requirements in DATA_POLICY.md and ignore local data/output directories. No market-data file or feed is added by this documentation change.

## 2026-10-07 — Quality reporting and CSV import

- Keep quality inspection read-only and parsing separate from mathematical aggregation.
- Use explicit date/decimal formats and exact column/instrument mappings; require a complete date format rather than implicitly choosing a year.
- Reject blank numeric cells by default. Permit only explicitly approved blank omissions, retaining their source line numbers; do not treat invalid numeric text as missing.
- Validate selected rows and duplicates before missing-value or date-cutoff omissions. Record filters and omissions separately; do not hide malformed later rows behind a cutoff.
- Keep original physical CSV line starts through multiline records and chronological sorting. Report input issues before approved omissions, distinct from the prepared output frame.
- Use synthetic public examples and tests. Private files can exercise the reader locally without being committed or publishing their calculated prices.

## 2026-10-07 — Equal-year profiles and local HTML

- Use an explicit reference date; exclude its entire calendar year from exactly the preceding N-year baseline. Missing years do not expand the window.
- Give available yearly monthly means equal weight, independent of daily observation counts. Show contributor years and observations beside each month; counts do not certify trading-session completeness.
- Define profile extrema over yearly monthly means. Keep input-unit levels and absolute differences; no percentage-return or forecast interpretation is introduced.
- Mark the cutoff month as partial unless it is the last calendar day, including leap February. This compares partial current-month observations with historical full-month means; the mismatch is visible rather than extrapolated away.
- Preserve full-input validation before cutoff/window selection. All-missing selected subsets are valid with NaN statistics and zero counts; numeric overflow remains an explicit error.
- Add standalone local HTML with inline SVG and tables, escaping labels and retaining chart gaps. No chart dependency, hosted service or graphical upload workflow is added. Rendered values use 12 significant digits; CSV export remains separate work.
- Command-line output is explicit and refuses overwrite or input aliases. Private reports are produced outside the public repository; only an invented synthetic CSV and its HTML example can be committed.

## 2026-10-07 — Readable chart axes and legend

- Fit line-chart axes to observed levels instead of forcing zero. Currency rates need a useful visible range. Use a shared domain across the 5/10-year charts of one instrument, including both baselines' extrema and the current line, with 8% margin.
- For constant levels use a 1% level margin (all-zero fallback -1 to 1). Clip only representational overflow at float64 limits; decimal/adaptive-precision tick labels and adaptive label space handle narrow and extreme ranges.
- Put a visual legend inside every SVG so screenshots retain the meaning of colors and shapes. Explicitly distinguish the historical range of yearly monthly means from daily highs/lows. Statistical definitions and table values are unchanged.

## 2026-10-07 — Private state and extended local exploration

- Keep SQLite as an explicit private file outside the public source checkout; persist hosted state only in a separate private data repository, requiring configuration before any schedule is claimed active.
- Preserve source/quote definitions per ID and audit inserted/revised values. Source/quote conflicts require distinct IDs. Reserved direct ECB IDs cannot be populated by CSV.
- Derive USD/PLN from daily same-date ECB quotations, then aggregate; use a 90-day re-fetch for missed runs/revisions and explicit full history for bootstrap/recovery.
- Treat futures input as continuation session closes with roll/adjustment definitions recorded. A delayed final trade or individual-expiry settlement does not automatically reproduce that history. The automatic continuation-close collector remains open.
- Add observation-based SMA, immediately preceding-calendar-month returns, first-observed annual indexing, matched day-of-month comparisons and exact-date FX conversion. Expose partial months, missing observations and normalization bases.
- Provide a loopback-only CSV import app and private standalone explorer. The standalone embeds observations, supports exploration/export, and requires the local app for imports. English labels explain every line/range; Python computes axis variants so browser toggles retain narrow/extreme precision.
- Keep the public explorer completely invented, including its synthetic FX. Independent review found and closed reserved-ID CSV relabeling, future-dependent coverage and daily-axis precision defects.

## 2026-10-07 — Five-year price comparison and technical chart

- The requested recent-price chart includes the current calendar year: exact year−4 through year. Keep the separate current-excluded seasonal baselines unchanged. Give available yearly monthly means equal weight, show contributor counts and include observed partial current months without projecting future prices.
- Adopt explicit Bollinger20 parameters: population standard deviation ddof0, multiplier2. SMA20 is already the middle band; price + SMA20/100/200 + upper/lower equals six displayed lines.
- Calculate rolling indicators from the entire cutoff-visible history before applying the trailing 12-calendar-month plot interval. Use observations, not invented weekend/session rows, and keep full-window minima. Retain the prior SMA20/50 API for backward compatibility.
- The month-row matrix mirrors the supplied price-comparison example. Its last-ten-year window includes the current year; colors compare unrounded monthly means with the last daily observation in each selected unit view. The reference observation date is visible, so an older available quote is never presented as today's price. Existing five-year charts and tables remain separate.

## 2026-10-08 — Market context and browser privacy

- Adopt explicitly dated market comparisons, current-inclusive midpoint empirical percentiles, Wilder14 smoothing, unannualized sample log-change volatility and correlations of exact matching percentage-change intervals. Preserve original strict validation and zero/negative level support with unavailable percentage views where necessary. See docs/METHODS.md for formulas and limits.
- Split PLN benchmark changes into commodity,currency andinteraction terms; never omit the product term. Require compatible metadata for automatic FX pairing and prevent private browser CSV observations from joining invented sample FX. Scenarios use declared hypothetical inputs and explicit quantities; no forecast or executable-quote claim.
- Browser CSV processing stays entirely in current-tab memory with no network or persistent browser storage. It requires one selected series,ISOdates,explicitdialect/cutoff and12MiB/20,000-row limits. Keep the server-backed private SQLite workflow separate; no XLSX claim.
- Use small source-only connector commits and GitHub-side reproducible generation for large public pages. Verify candidate provenance, tests and tree equality before a checked fast-forward; then verify Pages and actual browser behavior.
