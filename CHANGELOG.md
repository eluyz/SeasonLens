# Changelog

## Unreleased — 2026-10-07

- Read-only quality reports for prepared daily series, including source-row mappings.
- Explicit local CSV import with instrument selection, auditable blank-value omissions and date cutoffs.
- Synthetic CSV-to-monthly command-line example; no UI, XLSX reader or external data feed yet.

## 0.0.1 — Experimental checkpoint, 2026-10-07

- Initial project configuration and monthly aggregation contract.
- Monthly means/counts implementation, synthetic example and nine acceptance tests.
- Explicit errors for aggregation overflow and unsupported wider floating-point types.
- Initial import into the public repository with English documentation; no release tag yet. See STATUS.md for completed validation.
