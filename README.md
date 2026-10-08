# SeasonLens

An open-source project for auditable seasonality and market analysis of CSV time series and Excel master files.

**Current milestone: an interactive public demo, private SQLite persistence, direct ECB reference-rate updates and local CSV analysis (experimental 0.0.1 source checkpoint).** Private browser XLSX master-file import is implemented. Automatic futures continuation closes and a tagged release remain unimplemented.

The CSV reader prepares one explicitly selected series; the core computes monthly means and observation counts in a year-by-month grid. Missing months stay NaN with count zero. Entire intervening years are retained. Counts show data availability; they do not prove that all trading sessions are present.

## Browser demo

For a first visit, expand **Start here**: explore examples, download the invented six-series XLSX template, privately import a file or create a report. See the [step-by-step browser guide](docs/GETTING_STARTED.md). Wide tables and charts scroll inside their frames on small screens.

The [public browser demo](https://eluyz.github.io/SeasonLens/) is hosted on GitHub Pages from `docs/index.html`. It includes invented wheat, corn, rapeseed, EUR/PLN, EUR/USD and derived USD/PLN observations only. All three commodities support EUR/t and exact-date synthetic PLN/t views. See [deployment instructions](docs/PAGES.md) for publishing source and rebuild details.

The demo supports instrument/unit selection, monthly tables, six-line technical analysis, market snapshots, historical price positions, commodity/FX attribution, index-100 comparisons, volatility, RSI, correlations, wheat/corn spreads, seasonal distributions and scenario calculations. Open an XLSX master file or one CSV series directly in the browser without uploading it to a server; imported series stay in tab memory and disappear on reload. The local app additionally maintains an auditable private SQLite history. To rebuild the invented built-in samples, run `PYTHONPATH=src python3 examples/build_pages.py`.

Browser CSV import requires explicit date/value columns, units, delimiter, decimal convention and cutoff. Dates use `YYYY-MM-DD`; blank prices reject unless you explicitly allow their omission. Duplicate dates and invalid numbers always reject, including rows after the cutoff. Browser import does not overwrite built-in samples, impersonate an official data source or save data between visits. For XLSX worksheet/column mapping and supported Excel dates, see [Private Excel master-file import](#private-excel-master-file-import).

See [market analysis methods](docs/METHODS.md) for reference dates, percentile ties, RSI warmup, unannualized volatility, currency attribution, exact-interval correlations and the limits of futures continuation prices.

The **Statistical analysis** section adds historical buyer/seller VaR and Expected Shortfall, benchmark stress paths, completed-year monthly-change stability, commodity/FX variance contributions and walk-forward comparisons of three fixed forecasting baselines. Panels calculate when opened. Sample sizes, evaluation dates, missing-data reasons and assumptions remain visible. These descriptive statistics do not establish predictive power or investment profitability.

Supply-and-demand context is a separate panel with invented examples and private normalized CSV import. It shows dated stocks-to-use estimates and revisions, without automatically joining them to prices. See [fundamental CSV instructions](docs/FUNDAMENTALS.md) and the [statistical definitions](docs/SCIENCE_SPEC.md). No automatic fundamental-data feed is configured.

**Analysis options** keeps instrument/unit selection and the cutoff accessible while scrolling. **Export report** builds a selected-section snapshot with charts, tables, settings and methods. Preview it, use **Print / Save PDF** through the browser's print dialog, or download a script-free HTML copy. Reports stay local and can contain private results. See [quick controls and report instructions](docs/REPORTS.md).

## Quick start

Python 3.10+ is declared; this checkpoint was developed with Python 3.12 and pandas 2.2.3. This dependency is pinned for reproducibility.

Clone the repository and enter the project directory:

```bash
git clone https://github.com/eluyz/SeasonLens.git
cd SeasonLens
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

Or on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install and run the synthetic example:

```bash
python -m pip install -e .
python examples/monthly_demo.py
python examples/csv_demo.py examples/data/synthetic_prices.csv --instrument SYNTHETIC_A --skip-missing
python examples/seasonal_demo.py examples/data/synthetic_seasonal_prices.csv --instrument SYNTHETIC_GRAIN --as-of 2026-10-06 --skip-missing --unit "Synthetic units"
python -m unittest discover -s tests -v
```

Open `outputs/seasonal_report.html` in your browser to see the two charts and tables. A pre-generated synthetic example is also included as [examples/seasonal_demo.html](examples/seasonal_demo.html): download/open the file locally; GitHub displays its source. The command refuses to overwrite an existing report; use `--output outputs/another_report.html` for another run.

All example values are invented, not real market prices. There is no API key or market-data subscription requirement.

## Method

For each year and calendar month, calculate the arithmetic mean of that month's observations. There is no filling, interpolation or replacement of missing observations with zero. Zero and negative numeric values are valid. Input data are not modified.

The core accepts timezone-naive pandas datetime columns at midnight and finite real numeric values, with floating-point precision up to 64 bits. It rejects ambiguous or unprepared dates, missing values and duplicate dates. If a calculation overflows or produces a nonfinite group mean, it raises an explicit error rather than returning an invalid result.

## Local CSV import

Use explicit column names, date format, delimiter and decimal separator. For a long-format master, choose one instrument; dates shared by different instruments must not be combined into a single series.

A file with the standard `instrument_id` header requires an explicit instrument selection. For files using another identifier header, supply its name and selection yourself; without a filter, you are declaring that the input is one series. The supported CSV dialect follows Python's `csv.reader` in strict mode with doubled quote escaping, rather than a full RFC-conformance validator.

```python
from seasonlens import aggregate_monthly, import_csv

result = import_csv(
    "examples/data/synthetic_prices.csv",
    date_column="date", value_column="value", date_format="%Y-%m-%d",
    delimiter=",", decimal=".",
    instrument_column="instrument_id", instrument="SYNTHETIC_A",
    missing_values="skip",  # Explicit permission to omit blank value cells.
)
print(result.skipped_missing_rows)
monthly = aggregate_monthly(result.frame)
```

Blank values reject import by default. `missing_values="skip"` permits only empty/whitespace value cells, retaining their original physical line numbers in `skipped_missing_rows`. Invalid dates, numeric text, nonfinite numbers and duplicate dates always reject import, including a duplicate with a blank value. Zero and negative numeric values are valid. There is no filling, interpolation or duplicate repair.

`CSVImportError.report` explains rejected input with issue codes and source rows. On success, `result.report` describes selected input **before** authorized blank omissions, so `report.has_errors` can still be true when only accepted missing-value issues remain. `result.frame` is the clean chronological series; `source_rows` matches its order. Other-instrument and cutoff omissions are recorded separately. `inspect_series(frame)` is also available for prepared DataFrames and never changes them.

Date formats must specify `%Y`, `%d` and `%m`, `%b` or `%B`; the reader does not supply a missing year. Timezone directives `%z` and `%Z` are unsupported. `skip_rows` explicitly skips physical preamble lines before the CSV header. `max_date=datetime.date(...)` explicitly excludes later observations **after validation**, so a malformed later observation or duplicate still rejects input. No date cutoff is inferred from today's date. Thousands separators and direct XLSX input are unsupported by this Python CSV reader; XLSX browser import is described below. Units, quote conventions, price types and data-source permissions remain external metadata; importing does not change them.

Monthly averages describe historical levels. They do not establish predictive seasonality, remove inflation, or correct futures rolling effects.

## Equal-year profiles and reference year

```python
from datetime import date
from seasonlens import analyze_seasonality, render_seasonal_report

profiles = [analyze_seasonality(result.frame, as_of=date(2026, 10, 6), window_years=n)
            for n in (5, 10)]
print(profiles[0].profile)  # mean, minimum, maximum, years and observations
print(profiles[0].current)  # reference-year mean, count, difference, calendar status
html = render_seasonal_report(profiles, title="Local analysis", unit="Original input units")
```

The reference date is explicit; it is never the computer's implicit today. For a 2026 cutoff, 5 years means exactly **2021–2025** and 10 years means **2016–2025**. The reference year is excluded from both baselines. Older observations do not replace missing years. The mean gives each available year's monthly mean one equal weight. Historical minimum/maximum are extrema of those yearly monthly means, not daily highs/lows or a confidence interval. A year with only one observation still contributes, so inspect the counts before interpreting a profile.

For example, January 2024 observations 100 and 120 give 110; January 2025 observation 200 gives 200. Their equal-year profile is **155**, with historical min/max **110/200**, 2 contributing years and 3 observations. This differs from pooling all daily observations.

The reference-year line uses observations on or before the inclusive cutoff. Difference means reference monthly mean minus baseline mean, in original units; it is not a percentage return. Future dates remain excluded and counted, with validation of the entire input first. A mid-month reference mean is compared with full historical calendar months and is marked **Partial calendar month** (hollow orange marker). **Calendar month ended** describes a calendar boundary, not complete trading-session coverage. Missing chart points remain gaps. Each chart includes a visual legend for both lines, the historical min–max band and partial-month marker. The Y-axis automatically fits the plotted values with a small margin, without forcing zero; the 5/10-year charts share a scale for comparison. Profile means are monthly levels, not a normalized seasonal performance strategy or forecast.

`render_seasonal_report` returns a self-contained HTML string with inline SVG and tables, without writing or networking. Table values display 12 significant digits. The command-line example writes one report for one explicitly selected instrument, supports the CSV mapping/format options and protects the input and existing output. Generated reports from restricted inputs must remain private. The interactive explorer adds instrument selection, daily lines/SMA, CSV export and the local import form described below.

## Development

The implementation is assisted by coding agents. Mathematical requirements and hand-calculated cases guide review. See [SPEC.md](SPEC.md) for the API contract, [STATUS.md](STATUS.md) for verified progress, and [BACKLOG.md](BACKLOG.md) for planned work. Bug reports and usability feedback are welcome through [GitHub Issues](https://github.com/eluyz/SeasonLens/issues). Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.

The code is MIT licensed. Example data are synthetic and included under the same license. Licensed market data should not be added to this project without confirmed redistribution rights.

## Data boundaries

Imported market data and analyses generated from restricted inputs remain private by default. Public examples currently use synthetic values. Future public FX examples will use ECB reference rates with attribution and marked calculations. Direct Euronext delayed trade files are a separate candidate subject to their own distribution terms; this does not authorize publication of existing imported futures histories. See [DATA_POLICY.md](DATA_POLICY.md) for source-specific conditions and local storage conventions. The direct ECB downloader is implemented; automatic futures downloads are not configured.

## Interactive explorer and private database

Generate an entirely invented, self-contained demo and open it locally:

```bash
python examples/explorer_demo.py
```

Open `examples/explorer_demo.html`. Every observation, including FX, is invented. The standalone explorer works without a server; CSV import requires the local app. It contains:

- Six-line technical chart: daily price, full-window SMA20/SMA100/SMA200 and Bollinger upper/lower (20 observations, ±2 population standard deviations), with toggles and 90-day/12-calendar-month/full-history ranges.
- Monthly average prices for exactly five calendar years including the cutoff year, plus their equal-year monthly mean.
- Original-unit 5/10-year seasonal levels and normalized monthly index profiles.
- Monthly close-to-close changes, with missing/partial months visible.
- Matched partial-month comparisons through the same calendar day of preceding years.
- EUR/t to PLN/t using exact-date ECB EUR/PLN matches (synthetic FX only in the invented demo).
- Observation count, last date, age against the cutoff and missing calendar months.
- CSV export of selected observations/SMA; graphical CSV import into a private database.

Create data **outside this public source checkout**:

```bash
python -m seasonlens.cli --db ../seasonlens-private/seasonlens.sqlite init
python -m seasonlens.cli --db ../seasonlens-private/seasonlens.sqlite update-ecb --history
python -m seasonlens.app --db ../seasonlens-private/seasonlens.sqlite --as-of 2026-10-06
```

Open `http://127.0.0.1:8765`. Select a CSV, set its columns/date format, choose an instrument if applicable, supply the source/quote definition and explicitly allow blank omissions if wanted. An empty database can start the import screen without an ECB download. CSV imports cannot write reserved direct ECB IDs; give other sources distinct IDs. Existing source/unit/quote metadata are immutable, preventing accidental provider mixing. The app binds only to loopback, not a public network. It uploads the file to that local process.

For repeated files, use the same series ID and metadata. Dates are unique per series; new dates are inserted, corrected observations receive a revision record, unchanged values retain their observation timestamp. Imports are atomic. Omitting a date does not delete or fill it. Graphical imports retain original provenance and existing history. Future observations are validated and stored but excluded from a report before its explicit cutoff. Raw observations are embedded in standalone HTML, so restricted outputs stay private.

Nightly ECB refresh re-reads the last 90 days to recover short interruptions and revisions:

```bash
python -m seasonlens.cli --db ../seasonlens-private/seasonlens.sqlite update-ecb
python -m seasonlens.cli --db ../seasonlens-private/seasonlens.sqlite backup --output ../seasonlens-private/backup-new.sqlite
python -m seasonlens.app --db ../seasonlens-private/seasonlens.sqlite --as-of 2026-10-06 --output ../seasonlens-private/explorer-new.html
```

After an interruption longer than 90 days, use `update-ecb --history`. Backups/exports/snapshots refuse existing output paths. `--as-of` controls report calculations; change it when generating a new day's report. Updater cutoffs default to the current Warsaw calendar date and reject future-dated ECB responses. A fresh reference rate can still be yesterday's rate on a nonpublication day.

SQLite is a file, not a hosted service. Local use requires keeping that file and backups on your own disk. For unattended hosting, `examples/private_nightly.yml` is an **inactive template** for a separate **private data repository**: it seeds futures once from private inputs, obtains FX history directly from ECB, backs up, refreshes, generates a private snapshot and commits state there around 02:17 Europe/Warsaw. It does not enable a job in this public project. GitHub schedules can be delayed. A private repository and its runner must be configured before claiming unattended operation. See [docs/OPERATIONS.md](docs/OPERATIONS.md).

## Additional calculation definitions

SMA uses the previous 20/50 observations, not calendar days. Monthly change uses the last observed value divided by the immediately preceding calendar month's last observed value minus one, times 100. It is not a certified settlement return; a missing calendar month breaks the calculation. Normalization divides each daily positive value by that year's first observed positive value and multiplies by 100; monthly means of those index levels can differ from 100 even in the first month. Base dates and values are visible. Both return and normalized views require strictly positive input; other level views still accept zero/negative values. No futures roll adjustment or investable-return interpretation is supplied.

Matched partial-month comparison takes only the cutoff month's observations through the same calendar day in each exact preceding N-year window. February 29 clamps to February 28 in non-leap years. Each available year's mean gets equal weight. The matched cutoff removes a full-month/partial-month mismatch; it does not equalize session counts. Currency conversion matches dates exactly and reports unmatched observations, with no forward-fill.

## Five-year prices and six-line technical chart

The primary monthly-price comparison includes the cutoff year: at a 2026 cutoff it displays 2022–2026, one line per year and a black dashed period mean. Each available year's monthly arithmetic mean has equal weight. Missing years/months are not replaced with older history. The current partial month contributes only its available observations; later months' period mean uses available preceding years. The table shows contributor counts. This differs deliberately from the separate seasonal baseline, which still excludes the current year.

The technical chart defaults to the last **12 calendar months**, including both date endpoints. Indicators are calculated using all cutoff-visible earlier history before restricting the plot, so SMA200 can be present at the first displayed date. Exactly six lines are on by default: price, SMA20, SMA100, SMA200, Bollinger upper and Bollinger lower. Bollinger = SMA20 ± 2 × population standard deviation of the last 20 observations (`ddof=0`); SMA20 already is its middle line. Each rolling indicator requires its full observation window. Missing sessions/weekends are not inserted. CSV export contains the full cutoff-visible history and these six columns, irrespective of chart zoom.

The monthly price matrix places months in rows and the exact last ten calendar years (including the current year) in columns. Cells compare each monthly mean against the last available daily observation through the cutoff: green below, red above, blue equal, gray missing. The reference price, observation date and units are shown beside the table. Partial current months carry an asterisk; observation counts appear on hover. Comparisons use unrounded values in the selected display units, including exact-date PLN/t conversions. Colors describe historical levels, not trade recommendations.

Display conventions: the ten-year Monthly average prices matrix displays commodity prices as whole units and FX quotes with three decimal places, for display only. Other tables retain their decimal precision. Tables use — for unavailable values; future months are identified by hover text or calendar status. Underlying calculations, color comparisons and CSV exports retain full precision.

## Private Excel master-file import

The public explorer accepts .xlsx workbooks as well as single-series UTF-8 CSV. Files are read in browser memory without upload. Choose a worksheet, preview physical rows, set the header row and first historical data row, then select the date column and each instrument column. The default header row is 1 and first data row is 4, which leaves row 3 outside the historical selection for live quotes. Each price column needs explicit units and an instrument role; identities are not guessed.

Validation shows each instrument's first/last dates, observation count and blank/future omissions before a separate Add action commits the entire selection. Any changed setting invalidates that approval. Invalid selected rows, including malformed future rows and duplicate dates, reject the whole selection. Empty prices are skipped only with explicit permission.

Excel day numbers follow the workbook's 1900/1904 date system. Text dates use explicitly selected YYYY-MM-DD or DD.MM.YYYY. Dates with times and fictional 1900-02-29 reject. Numeric Excel cells do not depend on display decimal separators; numeric text uses the selected decimal convention. Saved formula values require explicit consent, may be stale, and are never recalculated. Macros, encrypted workbooks, external links and embedded objects are unsupported. Supported limits: 12 MiB file, 64 MiB expanded archive, 250,000 stored cells, 20,000 data rows per instrument, and 20 selected instruments.

Declaring EUR/PLN with units PLN per EUR in the same import group enables positive, exact-date EUR/t to PLN/t conversion, attribution and scenarios for that group's commodities. No sample FX or another private file is substituted. Explicit wheat/corn roles support same-group spreads in identical units. Missing quotes are never filled. Reload clears imported data; selected-series CSV export preserves observations and indicators.

Navigation links locate the main sections. Expandable explanations describe indicators and missing values. Only a strict list of view settings, built-in sample selections and line visibility is remembered in this browser. Imported observations, workbook details, private titles/IDs, cutoffs and scenario inputs are never persisted. Reset view settings clears the preferences without deleting in-memory imports. The bundled SheetJS reader is separately Apache-2.0 licensed; see src/seasonlens/vendor/README.md and LICENSE.
