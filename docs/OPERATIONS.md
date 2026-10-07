# Private data operations

Public repository: calculation code, tests and invented examples only. Private state: `seasonlens.sqlite`, accurate source metadata, inputs, backups and derived HTML. Do not put the private database in the public repository. SQLite itself is not encryption. Use a private disk/account or a separate private data repository with access restricted by its owner.

## State and update flow

The database contains `series` metadata, unique `(series_id, observation_date)` observations, revision audit and import logs. A transaction updates every declared series together or none. Source, unit, quote semantics and provenance cannot silently change for an existing ID. Dates absent from a new file remain unchanged. Re-importing an old file can intentionally revise observations back to its values; the nightly template therefore seeds the master only when the database does not exist.

`EUR_PLN`, `EUR_USD` and `USD_PLN` are reserved for direct ECB reference rates and cannot be imported through CSV. The prepared-data API is trusted: callers remain responsible for truthful provenance. USD_PLN is same-date EUR_PLN / EUR_USD, without rounding before storage. ECB rates describe a daily reference, not a session close.

For CLI master imports, metadata JSON is a list of objects with `series_id`, `title`, `unit`, `source`, `quote_semantics`, `provenance`; optionally `instrument` maps a differently named CSV instrument. The default long CSV layout is `date,instrument_id,value`; supply explicit mapping flags for another layout. Include futures/user series only; obtain reserved FX series through the ECB updater. Every declared series is validated before any transaction. Explicit `--skip-missing` permits blank cells and reports their source rows. `--as-of YYYY-MM-DD` excludes later dates after validation.

Example metadata for an invented import:

```json
[{"series_id":"SYNTHETIC_GRAIN","title":"Invented grain","unit":"EUR/t","source":"SYNTHETIC","quote_semantics":"Invented observations","provenance":"Invented example; no market feed"}]
```

Import using `python -m seasonlens.cli --db ../seasonlens-private/seasonlens.sqlite import-master examples/data/synthetic_seasonal_prices.csv --metadata ../seasonlens-private/metadata.json --skip-missing --as-of 2026-10-06`.

## Unattended private runner

Copy `examples/private_nightly.yml` to `.github/workflows/nightly.yml` in a separate private repository. Place authorized futures master/metadata under `inputs/master.csv` and `inputs/metadata.json`; these stay private. Give its runner write access only to that private repository. The public code checkout needs read access. Inspect and run the manual trigger first. State and reports are committed to the private repository; the public project never receives observations. First run seeds futures once and ECB history directly, subsequent runs refresh the last 90 days and record changes. A previous-state SQLite backup and latest private HTML are persisted.

The template schedule is 02:17 Europe/Warsaw to avoid the busiest minute; DST and queueing can shift execution. Standard private runners have plan quotas. This template is not an active hosted job, and no future execution has been verified. Local alternative: an operating-system scheduler runs the same commands on a machine that remains on. ChatGPT plan limits are not used by ordinary Python jobs.

Recovery: restore the private backup to a new path, check SQLite integrity and observation dates, then run the full ECB history updater if the outage exceeded 90 days. Retain independent backups; repository history is useful but not a complete disaster-recovery plan.

## Futures continuation closes

A continuation ticker identifies a rolled series, not one expiry. A matching daily-close feed must specify underlying expiries, roll dates and whether past prices are adjusted. A final trade, official settlement and a vendor continuation close can differ. Existing private continuation history is supported for import and analysis, with unknown roll/adjustment rules explicitly recorded. No automatic MATIF continuation-close collector is enabled. Do not append another contract/price definition under the same ID just because it concerns the same crop.

## Quality interpretation

Last observation and age are evaluated through the report cutoff. Missing months count the calendar interval from the first visible observation month through the cutoff month, independent of excluded future data; unknown if nothing is visible. No exchange session calendar is assumed. Coverage counts measure observations, not complete sessions. A report cutoff is explicit and a snapshot does not refresh itself.
