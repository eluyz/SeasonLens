# Project status

Date: 2026-10-07. Current checkpoint: experimental 0.0.1 with private SQLite, direct ECB updater, extended analytics and local interactive explorer. Earlier checkpoint sections remain historical records.

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

Configure a separate private data repository/runner and verify a manual update before enabling unattended execution. Verify a compatible MATIF continuation-close feed and its roll/adjustment rules. Full-browser/mobile QA, automated GitHub checks, XLSX import, alternatives validation and independent user feedback remain open. No hosted job or automatic futures feed is active.

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

## SQLite and extended explorer checkpoint — 2026-10-07

- Added private SQLite series/observations/revisions/imports, atomic inserts/corrections, immutable metadata, explicit backups/export and cutoff freshness. Data files stay outside this public checkout.
- Added fixed official ECB XML parser/downloader; last-90-day refresh, full-history opt-in, future-date rejection, same-date derived USD/PLN and source-isolated reserved IDs protected against CSV relabeling.
- Added observation SMA20/50, calendar-month close changes, normalized annual index with visible bases, matched partial-month means and exact-date PLN conversion without filling.
- Added loopback local CSV import app, empty-DB import screen and standalone multi-series explorer with controls, CSV export, coverage and embedded SVG legends. Public example is entirely invented, including FX.
- Added an inactive private-only nightly template that seeds futures once, obtains FX history directly, backs up, refreshes, renders and persists private state. No hosted job has been enabled or executed.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **101 tests passed**. This includes existing tests and hand-calculated analytics, revision/atomicity/source protection, source parser, CSV commands, exact-date conversion, future-independent coverage, escaping, localhost origins and empty-DB workflow.
- `python3 -m pip install --no-deps --no-build-isolation --target /tmp/seasonlens-v3-install-20261007 .`: wheel built and installed; installed `python -m seasonlens.app` ran from /tmp against an explicit private DB and wrote a standalone explorer. Packaged HTML assets were included. Existing dependency environment only, not a clean dependency download.
- Independent cross-review accepted analytics definitions and storage/report integration. Concrete defects in reserved-ID CSV relabeling, daily narrow/extreme axes and future-dependent missing-month counts were reproduced, repaired and rechecked. Daily axis variants now use the tested Python Decimal-axis logic.
- Actual embedded JavaScript executed in a Node DOM/control harness against the private explorer: instrument/PLN selection, 90/all/365 ranges and SMA toggles passed; CSV export retained all 4,292 selected cutoff observations irrespective of the visible 90-day range. Actual daily FX/PLN-grain SVGs rendered with Sharp and were visually inspected for readable fitted axes and legends. This is not a full-browser/mobile layout test; browser executables remain unavailable.
- Existing direct ECB history XML was parsed to seed private FX. Live recent-XML transport attempts with 10- and 5-second timeouts failed with URLError/timeouts in this environment. URL/timeout behavior is tested with fixture transport; a successful live download through the new updater remains unverified.
- Private six-series history/import omissions and derived explorer stayed outside the public repository. An independent 10-date ECB cross-rate/official NBP comparison is included only in the private delivery. No raw futures or real-price HTML has been published.

Limits: Python 3.12/pandas 2.2.3 only; no Windows/macOS/other-Python execution, full-browser QA, hosted schedule, compatible automatic futures collector, release tag, public adoption or OSS-program acceptance is claimed.

## Five-year prices and six-line technical explorer — 2026-10-07

- Explorer v4 shows monthly average prices for the exact last five calendar years including the current year, with an equal-year mean, contributor counts, gaps and partial-current-month markers. At the supplied cutoff these are 2022–2026. The earlier completed-year seasonal baselines remain separate.
- Technical analysis shows daily continuation prices, SMA20/100/200 and Bollinger upper/lower 20 (SMA20 ±2 population standard deviations). Windows use observed sessions and full cutoff-visible history before cropping to the last 12 calendar months. All six lines have explicit legends and independent toggles; axes fit the visible selections without forcing zero.
- `PYTHONPATH=src python3 -m unittest discover -s tests -q`: **115 tests passed**. Twelve new core cases and two dashboard cases cover hand calculations, missing/current years, future exclusion, warmup, narrow values, overflow and leap-year display cutoffs.
- Independent mathematical review confirmed arithmetic means, equal-year weights and population sigma. The actual embedded JavaScript passed all 63 nonempty line masks, the empty selection, 12m/90/all ranges, instrument/PLN selection, six yearly toggles and exact seven-column full-series CSV export. Actual private FX and grain SVGs rendered with Sharp; fitted axes and both two-row legends were visually inspected. This is bounded DOM/SVG validation, not a full-browser/mobile test.
- Real observations and private outputs remain outside the public checkout; public demonstration data are invented. No new data collection or unattended service was enabled.
- The final v4 wheel built and installed with existing dependencies; its packaged app and HTML assets generated a standalone private explorer from outside the checkout. The copied private SQLite file is byte-identical to the v3 snapshot.

## Month-row price matrix — 2026-10-07

- Explorer v5 adds a twelve-row monthly average price matrix for exactly the last ten calendar years including the current year. Columns are 2017–2026 for the supplied cutoff. Existing charts and tables remain available.
- Cells compare unrounded monthly means with the last cutoff-visible daily value in the selected display view: green lower, red higher, blue equal, gray missing. The reference value, actual observation date and units are explicit. Asterisks mark partial current months; hover text includes observation counts and comparison direction.
- `PYTHONPATH=src python3 -m unittest discover -s tests -q`: **117 tests passed**. New hand fixtures verify mean110 below reference155, mean200 above it, equality, future exclusion, the exact year window, missing cells, escaping and calendar-month-end markers; exact-date PLN conversion also exposes its own reference540.
- `node --check /tmp/seasonlens-v5-generated.js` passed for the actual generated private document. All nine private unit views have twelve rows, ten exact-year columns and dated reference labels. The regenerated public example uses invented observations only. The seven-file private delivery passed ZIP CRC checks and its SQLite snapshot is byte-identical to v4.
- Full-browser/mobile layout QA remains unverified. No data collector, hosted runner or automatic update was enabled.

- Independent review accepted matrix direction, exact cutoff/year window, missing/partial markers and separately converted PLN means/reference. The actual private-document JavaScript passed initial display, FX/grain Original/PLN switching and restoration; range/line controls preserve the matrix and seven-column CSV export retains all cutoff rows. This was a bounded DOM harness, not full-browser layout validation.

## Whole-unit prices and dash placeholders — 2026-10-07

- Explorer v6 labels the matrix Monthly average prices and displays its monthly values with zero decimal places. Other tables retain their existing precision. Numeric calculations, comparison colors and exports are unchanged.
- Unavailable numeric table values now display —; matrix/return future-month cells have neutral backgrounds and after-cutoff tooltips, while historical gaps remain gray and explicitly explained. Annual table hover text and seasonal report calendar statuses preserve the future/history distinction. Actual zero prices and zero contributor counts stay zero.
- `PYTHONPATH=src python3 -m unittest discover -s tests -q`: **117 tests passed** after updating existing presentation expectations. No new arithmetic behavior or tests were added. Actual generated JavaScript passed node syntax validation and git diff --check passed.
- All nine private unit views were parsed: matrix data cells are whole numbers (with optional partial-month star) or —, and no table uses a Missing value cell. Daily observations/indicators and chart axes match v5 exactly; the private SQLite snapshot is byte-identical. The seven-file private ZIP passed CRC validation. Regenerated public examples use synthetic observations only. Full browser/mobile validation remains unverified.
- Independent review found pandas date-table rendering could leave NaT in normalization-base rows despite na_rep. A copied display frame now formats base dates as ISO dates or — before HTML generation; analytical frames are unchanged.
- Final independent presentation review accepted whole-unit display with raw-value colors, no NaT/Missing cells in all 81 private tables, future-month styling and actual generated-JavaScript instrument/unit refresh. CSV values remained exact across the complete selected cutoff series. This remains bounded DOM validation, not a full browser test.

## Commodity/FX matrix precision — 2026-10-07

- Explorer v7 corrects the display convention: commodity monthly averages and references have zero decimal places; FX quotes and references have three. Currency-unit labels use the documented AAA per BBB form. Dash placeholders and full-precision calculations/exports are unchanged.
- `PYTHONPATH=src python3 -m unittest discover -s tests -q`: **117 tests passed**. No new tests were introduced for this reversible presentation adjustment. All nine private views were parsed to verify the correct number of decimal places in matrix data cells and the reference, with identical daily data, indicator values and axes versus v6. The private database is byte-identical; the regenerated seven-file ZIP passed CRC checks. git diff --check passed. The public example remains synthetic; no full-browser test or data update was performed.

## GitHub Pages demo preparation — 2026-10-07

- Added a reproducible, no-input public builder and `docs/index.html`, `docs/.nojekyll`, `docs/sample_prices.csv`, plus activation/rebuild guidance. All embedded observations, quotes and download CSV values come from the deterministic synthetic generator; no private database/report is a deployment input.
- The public page labels sample data explicitly, removes local-import controls and server handlers, blocks script connections through CSP, retains instrument/unit/range/line/CSV controls, and uses horizontal chart/table scrolling, touch-sized controls and collapsed advanced sections for narrow displays. Browser own-file import is explicitly unavailable; the local app remains linked.
- `PYTHONPATH=src python3 -m unittest discover -s tests -q`: **117 existing tests passed**. The generated public JavaScript passed node syntax checking; static localhost HTTP requests served both the HTML entry and sample CSV successfully. Source/payload scans found only SYNTHETIC provenance, no private series identifiers, local upload controls or server-request calls. git diff --check passed.
- Independent review found the intro insertion targeted an outdated controls tag. The builder now checks the exact panel tag before inserting it; regenerated HTML confirms the hero warning and navigation are present. No analytical code changed.
- GitHub repository metadata reports `has_pages=false`. Available GitHub connector operations can publish source files but expose no Pages-settings mutation, and no GitHub CLI is available. Repository administrator activation of `main` → `/docs` remains required. Do not report the expected project URL as live until deployment is verified. Full browser/device layout QA remains unverified.
- Final independent review approved deterministic synthetic source/CSV equality and public markup. Actual generated JavaScript passed instrument/PLN changes, 12m/90/all ranges, all 63 technical line masks, six annual toggles and full seven-column CSV export, with no API requests. This is bounded control/DOM validation, not full-browser/mobile visual QA.

## Public hosting activation and six sample series — 2026-10-07

- The owner enabled GitHub Pages with main → /docs. GitHub reported successful pages build and deployment run 37687557896 for commit 1d9d70d5c210b63f65fdd5805ffe80f7a6696708. Direct HTTPS requests subsequently returned 200 for the public page and sample CSV; the embedded payload contained only synthetic provenance. This supersedes the earlier activation-pending checkpoint.
- Expanded the deterministic generator and both public examples to six synthetic instruments: wheat, corn, rapeseed, EUR/PLN, EUR/USD and same-date derived USD/PLN. Wheat retains the SYNTHETIC_GRAIN identifier. Three commodities each have EUR/t and PLN/t views; currencies have original quote units. No private inputs or real exchange contract histories were published.
- `PYTHONPATH=src python3 -m unittest discover -s tests -q`: **117 existing tests passed**. Final public payload checks verified six synthetic sources, nine unit views and 3,330 cutoff-visible observations per view. Every derived USD/PLN value exactly matches same-date EUR/PLN divided by EUR/USD. Actual generated JavaScript passed node syntax checking. Existing math and private database were unchanged.
- Independent six-series review accepted deterministic source equality, exact derived cross-rate and all three exact-date PLN conversions. Actual public JavaScript selected all six instruments/nine views, refreshed tables and labels, rendered charts and exported complete accurate CSV series with zero API requests. Bounded DOM validation only; full browser/device visual QA remains unverified.

## GitHub-side demo build preparation — 2026-10-08

- All six sample instruments remain preserved in local commit 23ba04d96ebd18c2e7260e73fea46fc0a6d55939. Direct git push failed because the shell has no GitHub credential; the connected GitHub app reports repository push permission. No large publication JSON was reread.
- Prepared a small source-only update and a GitHub Actions builder, pinned to verified checkout/setup-python commit SHAs, Python 3.12.14, pandas 2.2.3 and NumPy 2.3.5. The builder runs the existing analytical tests, regenerates both invented pages, checks six SYNTHETIC instruments/nine views, and saves only generated public files on a unique candidate branch. Promotion to main must use an expected-head fast-forward through the authorized connection, because workflow-token pushes do not trigger Pages.
- Workflow YAML, embedded Python and shell syntax checks passed locally. Remote workflow execution, source publication and six-instrument public deployment are pending verification. No private input is used.

## Six-instrument public publication verified — 2026-10-08

- Source-only commit 7baa9eab74ee1ab95869dfb19c07cb8b8357d447 published seven small files through the existing authorized GitHub connection. No large publication JSON or page contents were transferred through chat.
- GitHub build run 37749343123 completed successfully: 117 tests passed and both pages passed the six-SYNTHETIC-instrument/nine-view guard. Its generated commit 4b753c86ef0a85ddaee1ee5bd9b976a609b7b57e changed only docs/index.html and examples/explorer_demo.html; the complete tree was byte-for-byte identical to the preserved local implementation.
- Promoted that direct child to main with an expected-head fast-forward. Pages build/deployment run 37749604633 completed successfully for the generated commit. Direct public HTTPS returned 200 and exactly six synthetic instruments/nine views. All 7,287,963 page bytes matched the verified commit (SHA-256 04da32a8ed74646ece08a907814f11c7ce43d5f5ab8bc812ca472e2f6dffe9fc).
- Local checkout synchronized cleanly to the published generated commit; original local commits remain on checkpoint/six-instruments-before-publication. Full browser/device visual QA remains unverified. This completes the pending six-instrument publication checkpoint above.
