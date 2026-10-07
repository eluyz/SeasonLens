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
