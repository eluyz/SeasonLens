# SeasonLens

An open-source project for auditable seasonality analysis of CSV and Excel time series, starting with a small monthly aggregation core.

**Current milestone: monthly aggregation core only (0.0.1).** This is an experimental source checkpoint, not the complete v0.1 application or a published PyPI package. CSV/XLSX import, multi-year seasonal profiles, charts, reports and UI are still planned.

The current function accepts a prepared pandas DataFrame, computes monthly means and observation counts, and returns a year-by-month grid. Missing months stay NaN with count zero. Entire intervening years are retained. Counts show data availability; they do not prove that all trading sessions are present.

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
python -m unittest discover -s tests -v
```

All example values are invented, not real market prices. There is no API key or market-data subscription requirement.

## Method

For each year and calendar month, calculate the arithmetic mean of that month's observations. There is no filling, interpolation or replacement of missing observations with zero. Zero and negative numeric values are valid. Input data are not modified.

The first core accepts timezone-naive pandas datetime columns at midnight and finite real numeric values, with floating-point precision up to 64 bits. It rejects ambiguous or unprepared dates, missing values and duplicate dates. If a calculation overflows or produces a nonfinite group mean, it raises an explicit error rather than returning an invalid result. A later import/quality layer will explain how to prepare real files.

Monthly averages describe historical levels. They do not establish predictive seasonality, remove inflation, or correct futures rolling effects.

## Development

The implementation is assisted by coding agents. Mathematical requirements and hand-calculated cases guide review. See [SPEC.md](SPEC.md) for the API contract, [STATUS.md](STATUS.md) for verified progress, and [BACKLOG.md](BACKLOG.md) for planned work. Bug reports and usability feedback are welcome through [GitHub Issues](https://github.com/eluyz/SeasonLens/issues). Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.

The code is MIT licensed. Example data are synthetic and included under the same license. Licensed market data should not be added to this project without confirmed redistribution rights.

## Data boundaries

Imported market data and analyses generated from restricted inputs remain private by default. Public examples currently use synthetic values. Future public FX examples will use ECB reference rates with attribution and marked calculations. Direct Euronext delayed trade files are a separate candidate subject to their own distribution terms; this does not authorize publication of existing imported futures histories. See [DATA_POLICY.md](DATA_POLICY.md) for source-specific conditions and local storage conventions. Data downloads are not implemented yet.
