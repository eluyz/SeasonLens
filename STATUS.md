# Project status

Date: 2026-10-07. Checkpoint: experimental 0.0.1 source with CSV preparation and monthly core.

Repository: https://github.com/eluyz/SeasonLens. This source checkpoint is the first code import after the owner's repository initialization. Documentation is in English. No release tag has been created.

## Complete

- Project skeleton, MIT license, documentation, agent instructions and backlog.
- SL-001: aggregate prepared daily observations into calendar-year/month means and observation counts.
- Visible absent months and intervening years; no silent filling or input mutation.
- Strict prepared-input validation and explicit numeric-range errors.
- Synthetic runnable example.
- SL-002: read-only prepared-series quality reports with source-row issue locations.
- SL-003: explicit CSV parsing, instrument selection, auditable missing-value and cutoff omissions.
- Synthetic CSV-to-monthly command-line example.

## Validation

Environment: Python 3.12.14, pandas 2.2.3, NumPy 2.3.5.

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 9 tests passed after review fixes.
- `python3 -m pip install --no-deps --no-build-isolation --upgrade --target <temporary-target> .`: final wheel built and package installed successfully using existing environment dependencies.
- Demo run with installed package: January 2024 mean 110/count 2; all of 2025 absent; February 2026 mean 200/count 1.
- Independent agent review found overflow and unsupported long-double handling. Both were repaired with explicit ValueError and regression tests.

This is not a clean dependency-download or cross-platform installation test. Python versions other than 3.12 and Windows/macOS have not been executed. No UI, XLSX importer, multi-year profiles, charts, report export, external user adoption, background runner or OSS-program application has been verified or implemented yet.

## Next

SL-000: alternatives/need validation remains open. Technical next task is SL-004 equal-year 5/10-year profiles. Automated GitHub checks (SL-001A) are still planned. Use the original SeasonLens plan as context; this file records current implementation progress.

No user data are needed for the next implementation tasks. The owner has connected this repository and authorized the initial import. Automated GitHub checks are a planned next step; local test results above are the currently verified evidence.

## Data-policy update — 2026-10-07

- Documented public code/private imported market data and private derived outputs in DATA_POLICY.md.
- Selected direct ECB reference rates for future public FX examples; documented conditional Euronext delayed trade files separately from existing imported histories.
- Added root local-input/output directories to .gitignore and linked the policy from README.md.
- Reviewed official ECB/Euronext source conditions and the changed documentation. No calculation code changed, so the earlier mathematical test results are unchanged; no new unit-test run was needed for this documentation update.
- No downloader, new input file, public market-data dataset or chart has been added. Git ignore patterns are safeguards, not access control.

## CSV and quality checkpoint validation — 2026-10-07

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 35 tests passed, including the unchanged mathematical core and synthetic parsing/quality cases.
- `PYTHONPATH=src python3 examples/csv_demo.py examples/data/synthetic_prices.csv --instrument SYNTHETIC_A --skip-missing`: January 2024 mean 110/count 2; blank source line reported; absent 2025 retained; February 2026 mean 200/count 1.
- `python3 -m pip install --no-deps --no-build-isolation --target /tmp/seasonlens-csv-install-20261007 .`: wheel built and installed successfully with existing environment dependencies. The synthetic CSV demo also passed using that installed package from outside the source checkout.
- Local private smoke checks imported six series and reconciled their observations, monthly counts and independently calculated sample means. The input file stayed unchanged; no private price values or derived tables were published.
- The independent reviewer found timezone-name parsing could erase a timezone and duplicate auxiliary columns could escape inspection. Explicit timezone-directive rejection and whole-header duplicate detection fixed both; regression tests and reviewer probes verified the fixes.
- Standard instrument_id master files now require a selection. Other identifier conventions require caller-supplied mapping. The supported Python CSV dialect is documented, without claiming full RFC-conformance validation.
- A first exact private FX comparison used pandas' default decimal parser, which can differ at floating-point rounding precision. The final independent comparison used round-trip parsing and reconciled every imported value exactly; no importer or source data change was required.

Validation remains local Python 3.12/pandas 2.2.3, not cross-platform or dependency-download testing. Quality reports describe selected input before explicitly accepted omissions; a successful import can retain missing-value issues in that input report. No public data feed, graphical interface or seasonal profile has been implemented by this checkpoint.
