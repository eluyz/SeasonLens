# Install SeasonLens 0.1.0

## Browser: no installation

Open the [public demo](https://eluyz.github.io/SeasonLens/) or follow the [wheat + EUR/PLN walkthrough](https://eluyz.github.io/SeasonLens/walkthrough.html). No account or API key is needed. Built-in prices and the workbook are invented. Files imported here remain in tab memory and disappear on reload.

The [v0.1.0 release](https://github.com/eluyz/SeasonLens/releases/tag/v0.1.0) also provides a frozen browser ZIP. Extract it into one folder and open `index.html`; keep `walkthrough.html` and the example workbook alongside it. This is optional and does not install a server or save private histories. The live demo can change after this release.

## Optional Python app

Use Python 3.10 or newer. Start with a versioned checkout:

```bash
git clone --branch v0.1.0 --depth 1 https://github.com/eluyz/SeasonLens.git
cd SeasonLens
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

If activation is unavailable, use the environment's Python directly: `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux. No execution-policy change is necessary.

Install the checkout and check its version:

```bash
python -m pip install .
python -c "from importlib.metadata import version; print(version('seasonlens'))"
seasonlens-data --help
seasonlens-app --help
```

Expected package version: **0.1.0**. Installation downloads declared dependencies from the Python package index. SeasonLens is distributed through this GitHub release; do not assume an unrelated package-index listing is this project.

Alternatively, download `seasonlens-0.1.0-py3-none-any.whl` from that release and run `python -m pip install /path/to/seasonlens-0.1.0-py3-none-any.whl` inside the activated environment. Wheels do not include the repository's development tests or example scripts; use the source checkout or source distribution for those.

## First local example

From the source checkout:

```bash
python examples/explorer_demo.py
```

Open `examples/explorer_demo.html`. All six series are invented. CSV/XLSX browser import and report download work in tab memory; they do not persist to SQLite.

For a persistent private CSV history, create a database **outside the public source directory**:

```bash
seasonlens-data --db ../seasonlens-private/seasonlens.sqlite init
seasonlens-app --db ../seasonlens-private/seasonlens.sqlite --as-of 2026-10-06
```

Open `http://127.0.0.1:8765`. The empty database opens a local CSV import form. Stop the local app with Ctrl+C. Use your own explicit analysis cutoff for your history; the date above matches the invented tutorial. The app binds to loopback and sends database imports only to that local process.

The browser XLSX wizard and persistent local CSV importer are different paths. XLSX imports do not update SQLite. Repeated persistent CSV imports with identical series metadata update dated observations atomically and record revisions. See [operations](OPERATIONS.md) for backups and the optional direct ECB updater. Neither this installation nor the release enables unattended jobs or a futures feed.

## Development checks

From the source checkout, install development tooling and run:

```bash
python -m pip install build==1.3.0 wheel==0.45.1 setuptools==80.9.0
python -m unittest discover -s tests -q
python -m build --no-isolation
```

Browser-module tests also require Node.js on PATH. Node is not required to use the public demo or installed Python app. The CI installation check runs the wheel in a second virtual environment, outside the checkout; its arithmetic, bundled assets, entry points and empty loopback app are checked by `scripts/check_installed.py`.

## Limits

- Version 0.1.0 is experimental. The Python API may change before 1.0.
- Browser imports: XLSX/CSV up to 12 MiB; strict dates, units, roles, duplicates and numeric validation. Old XLS/XLSM and external workbook links are unsupported. Formula caches require explicit consent and are not recalculated.
- Private imports and reports can contain restricted information. MIT covers code and invented examples; it does not grant rights to redistribute your market data.
- There is no automatic MATIF/CBOT/ICE close collector, hosted database or fundamental-data feed.
- Sample history has a fixed cutoff. Short histories retain absent months/years and insufficient-statistic messages.
- Print / Save PDF depends on the browser. Standalone HTML is the verified export fallback.
- Linux CI covers the declared minimum Python and Python 3.12. Physical phones, Safari and Windows/macOS execution are not claimed; see [recorded verification](../STATUS.md).
