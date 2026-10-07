# SeasonLens

An open-source project for auditable seasonality analysis of CSV and Excel time series, starting with a small monthly aggregation core.

**Current milestone: CSV import, quality reporting, monthly aggregation, equal-year profiles and local HTML charts (experimental 0.0.1 source checkpoint).** This is not the complete v0.1 application or a published PyPI package. XLSX import, CSV export, graphical file selection and public data downloads are still planned.

The CSV reader prepares one explicitly selected series; the core computes monthly means and observation counts in a year-by-month grid. Missing months stay NaN with count zero. Entire intervening years are retained. Counts show data availability; they do not prove that all trading sessions are present.

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

Date formats must specify `%Y`, `%d` and `%m`, `%b` or `%B`; the reader does not supply a missing year. Timezone directives `%z` and `%Z` are unsupported. `skip_rows` explicitly skips physical preamble lines before the CSV header. `max_date=datetime.date(...)` explicitly excludes later observations **after validation**, so a malformed later observation or duplicate still rejects input. No date cutoff is inferred from today's date. Thousands separators and direct XLSX input are not supported yet. Units, quote conventions, price types and data-source permissions remain external metadata; importing does not change them.

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

`render_seasonal_report` returns a self-contained HTML string with inline SVG and tables, without writing or networking. Table values display 12 significant digits. The command-line example writes one report for one explicitly selected instrument, supports the CSV mapping/format options and protects the input and existing output. Generated reports from restricted inputs must remain private. Local HTML reporting is implemented; interactive file selection, multi-instrument panels and CSV export are still pending.

## Development

The implementation is assisted by coding agents. Mathematical requirements and hand-calculated cases guide review. See [SPEC.md](SPEC.md) for the API contract, [STATUS.md](STATUS.md) for verified progress, and [BACKLOG.md](BACKLOG.md) for planned work. Bug reports and usability feedback are welcome through [GitHub Issues](https://github.com/eluyz/SeasonLens/issues). Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.

The code is MIT licensed. Example data are synthetic and included under the same license. Licensed market data should not be added to this project without confirmed redistribution rights.

## Data boundaries

Imported market data and analyses generated from restricted inputs remain private by default. Public examples currently use synthetic values. Future public FX examples will use ECB reference rates with attribution and marked calculations. Direct Euronext delayed trade files are a separate candidate subject to their own distribution terms; this does not authorize publication of existing imported futures histories. See [DATA_POLICY.md](DATA_POLICY.md) for source-specific conditions and local storage conventions. Data downloads are not implemented yet.
