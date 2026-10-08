# Start with SeasonLens

Open the [public demo](https://eluyz.github.io/SeasonLens/). No installation or account is needed. Expand **Start here** near the top of the page to choose a path.

## Explore an example

1. Open **Analysis options** and choose an instrument and display units.
2. In **Start here**, choose **View five-year prices** or **View monthly averages**.
3. Check the cutoff, legends and coverage. A dash means unavailable data, not zero. The six built-in samples are invented, with a fixed cutoff of 2026-10-06.

## Try the XLSX template

1. Choose **Download example XLSX template**. Its download also works in a standalone offline build, without a second server request.
2. Open **Read me** in the workbook. It contains six invented series and 210 weekday observations from 2025-12-17 through 2026-10-06. Its short history does not cover five or ten completed years.
3. Choose **Open private import**, select the file and choose **Open and preview file**.
4. Select worksheet **Prices**, header row **1**, first data row **4**, date column **A** and cutoff **2026-10-06**. Row 2 declares units; row 3 is an invented live example, excluded by first data row 4.
5. Select columns B–G and declare these units and roles explicitly. Names do not automatically assign identities.

| Column | Title | Units | Role |
| --- | --- | --- | --- |
| B | Wheat sample | EUR/t | Wheat |
| C | Corn sample | EUR/t | Corn |
| D | Rapeseed sample | EUR/t | Rapeseed |
| E | EUR/PLN sample | PLN per EUR | EUR/PLN |
| F | EUR/USD sample | USD per EUR | EUR/USD |
| G | USD/PLN sample | PLN per USD | USD/PLN |

6. Choose **Validate selected instruments**. Review six instruments with 210 observations each, then choose **Add validated instruments to this tab**. File imports are labelled USER_FILE; importing does not give them official-provider provenance.

To use your own history, replace every example observation from row 4 onwards. Keep one date per row and numeric quotes in the declared units. Use Excel date cells or the supported explicit text-date format. Set your own cutoff. Blank prices require explicit skipping; invalid or duplicate dates reject the selection. The template has no formulas and needs no cached-formula consent.

Same-workbook EUR/PLN can support an exact-date PLN view for the three EUR/t commodities. Private imports never substitute invented built-in FX. Imports stay in current-tab memory, disappear on reload and are not saved to SQLite. Export before leaving if you need a result to keep. Use the local app for persistent private history.

## Create a report

1. Select your instrument, units and settings.
2. Choose **Open report builder**, select sections and choose **Build report preview**.
3. **Download HTML** saves a self-contained report. **Print / Save PDF** uses your browser's print dialog; saving and pagination depend on that browser. Rebuild after changing settings.

Reports include visible selected results, provenance and methods. They omit the original observation arrays but may still contain private information. Importing or downloading does not publish a file. Sharing a downloaded report shares its visible results.

## Small screens

Charts and wide tables scroll horizontally inside their frames. Other controls fit the page width. On a keyboard, focus a frame and use arrow keys. Analysis options keeps the instrument and cutoff visible; Escape closes its menu. Long column mappings may be easier on a larger screen.

Contributors can use `docs/layout-check.html` to inspect the real public demo in one iframe at 320, 360, 390, 430 or 768 CSS pixels. This checks responsive browser layout, not physical phones, touch hardware or Safari. It uses the same local invented-data demo and adds no data service.

## Rebuild the template asset

The workbook is authored with `@oai/artifact-tool` using `examples/create_import_template.mjs` in a temporary Node workspace that resolves that dependency. This tool is not needed to run SeasonLens or rebuild its pages. After authoring, run `python examples/normalize_template_package.py <generated-xlsx>` to add the explicit workbook content-type declaration required by the strict importer. Only package declarations change; all worksheet values, formulas, relationships and styles remain byte-identical. Base64-encode the result into `src/seasonlens/import_template.xlsx.b64` and run the import-template tests before updating the public build. `examples/build_pages.py` decodes that asset into the public downloadable XLSX; it never reads private inputs.
