# Project status

Date: 2026-10-07. Checkpoint: experimental 0.0.1 source with CSV preparation, equal-year profiles and local HTML reporting.

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
- SL-004: exact-window equal-year profiles, contributor/observation counts, monthly-mean extrema and cutoff-limited reference-year comparison.
- Local standalone HTML/SVG report and synthetic CSV-to-report command-line example (partial SL-005).

## Earlier monthly-core validation

Environment: Python 3.12.14, pandas 2.2.3, NumPy 2.3.5.

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 9 tests passed after review fixes.
- `python3 -m pip install --no-deps --no-build-isolation --upgrade --target <temporary-target> .`: final wheel built and package installed successfully using existing environment dependencies.
- Demo run with installed package: January 2024 mean 110/count 2; all of 2025 absent; February 2026 mean 200/count 1.
- Independent agent review found overflow and unsupported long-double handling. Both were repaired with explicit ValueError and regression tests.

This is not a clean dependency-download or cross-platform installation test. Python versions other than 3.12 and Windows/macOS have not been executed. At the earlier monthly-core checkpoint, no UI, XLSX importer, multi-year profiles, charts or export existed. Later checkpoints below record added behavior. External user adoption, a background runner and an OSS-program application remain unverified.

## Next

SL-000: alternatives/need validation remains open. SL-004 is implemented. Technical next tasks are SL-001A automated checks and the SL-007 local file-selection workflow; CSV export (remaining SL-005) and XLSX import (SL-006) remain planned. Automated GitHub checks (SL-001A) are still planned. Use the original SeasonLens plan as context; this file records current implementation progress.

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

Validation remains local Python 3.12/pandas 2.2.3, not cross-platform or dependency-download testing. Quality reports describe selected input before explicitly accepted omissions; a successful import can retain missing-value issues in that input report. No public data feed, graphical interface or seasonal profile existed at the CSV checkpoint; seasonal profiles are added in the checkpoint below.

## Seasonal profiles and HTML checkpoint validation — 2026-10-07

- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: all 54 tests passed (35 existing, 13 seasonal, 6 report/workflow). Coverage includes unequal daily observation counts, exact windows, missing baselines, inclusive future cutoffs, leap February, explicit overflow, HTML escaping/gaps, compatible windows and no-overwrite input/output guards.
- `PYTHONPATH=src python3 examples/seasonal_demo.py examples/data/synthetic_seasonal_prices.csv --instrument SYNTHETIC_GRAIN --as-of 2026-10-06 --skip-missing --unit 'Synthetic units' --output examples/seasonal_demo.html`: produced the public synthetic example. It records one omitted blank, one other-instrument row and two valid future observations excluded from calculations.
- `python3 -m pip install --no-deps --no-build-isolation --target /tmp/seasonlens-seasonal-install-20261007 .`: wheel built and installed successfully with existing environment dependencies. The CSV-to-seasonal-report example also ran from /tmp using that installed package, producing a report outside the checkout.
- Independent mathematical/report review accepted the implementation. Separate probes confirmed the 155/110/200 hand example, cutoff behavior, unchanged input, absence of future sentinel values in HTML and explicit overflow handling.
- Local private checks independently recalculated every month for both 5/10-year windows across six series using standard-library grouping and math.fsum, reconciling means, extrema, contributor/observation counts and current differences within float64 tolerance. The private source hash remained unchanged. Private HTML outputs and their package are outside the public repository and are not committed.
- Both actual synthetic report SVG charts rendered successfully to PNG using the existing Sharp runtime; a chart was inspected for readable labels, historical band, reference line and partial-month marker. Full-page Playwright preview could not launch because browser executables are absent. HTML/table semantics and SVG XML were checked programmatically; full browser/mobile layout QA is still unverified.

Remaining limits: this is local Python 3.12/pandas 2.2.3 validation with existing dependencies, not clean dependency-download or Windows/macOS testing. No graphical file selector, live feed, CSV export, normalized-return model, external adoption, scheduled background runner or program acceptance has been implemented or verified. The HTML example uses invented data only; restricted input analyses remain private.

## Axis and legend correction — 2026-10-07

- Changed only chart presentation: automatic padded bounds across both profiles, no forced zero, equal scale for 5/10-year comparison, adaptive decimal labels and left label space. Embedded SVG legends name the two lines, historical range and partial-month marker.
- `PYTHONPATH=src python3 -m unittest discover -s tests -p test_report.py -v`: 10 report/workflow tests passed, including hand-calculated FX bounds 4.184–4.416 for levels 4.2–4.4, shared scales, narrow/constant/negative/subnormal/extreme values, legend meanings, escaping and no-overwrite behavior. Seasonal aggregation code did not change; the earlier full 54-test checkpoint remains the last full-suite run.
- Independent reviewer probes closed tick-label issues for adjacent float64 values, maximum values and minimum subnormals. Long-label space was also made adaptive following review.
- Regenerated synthetic and six private reports; every before/after calculation table matched exactly and the private input hash stayed unchanged. Rendered and inspected the actual private FX SVG with the embedded legend; private outputs remain outside git. Full browser/mobile layout QA remains unverified as recorded above.
