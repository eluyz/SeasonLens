# Start with SeasonLens

Open the [public demo](https://eluyz.github.io/SeasonLens/). No installation or account is needed. Expand **Start here** near the top of the page to choose a path.

For one complete workflow, follow the [wheat + EUR/PLN walkthrough](WHEAT_FX_WALKTHROUGH.md): import only two columns, verify the PLN conversion and export a report. The [web version](https://eluyz.github.io/SeasonLens/walkthrough.html) stays open beside the demo.

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

## Reuse an XLSX import profile

A profile avoids repeating the worksheet and column mapping for the next version of the same master workbook. It is a configuration file, not a saved history or an automatic update.

1. Open an XLSX workbook, set its rows, date column and selected instrument mappings, then validate successfully as above.
2. Choose **Save import profile** to save the JSON settings file locally. Keep it private: worksheet/header names and your instrument titles can reveal information even though observations are omitted. Download the profile before changing the validated settings.
3. Next time, select the updated XLSX workbook and choose **Open and preview file**. Choose your current analysis cutoff explicitly.
4. Select your JSON file under **Import profile JSON file** and choose **Load import profile**. It restores the worksheet, rows, date/value columns, titles, units, roles and number/text-date conventions only when the worksheet and selected column/header identities match exactly. A corrupt profile or changed selected layout rejects without partially replacing your settings. Correct the mapping manually and validate before downloading a replacement profile.
5. Check the preview. Loading retains your current cutoff and clears permission to skip blank prices or use cached formula values. Enable either permission again only if appropriate for this workbook.
6. Choose **Validate selected instruments**, review dates, counts and omissions, then choose **Add validated instruments to this tab**. Loading a profile alone never adds observations.

The profile excludes observations, workbook filename, cutoff and blank/formula permissions. It is not uploaded, synchronized or remembered automatically by the app. Imported prices still disappear on reload; a saved profile does not recover them. This feature supports XLSX only; CSV files retain their explicit manual settings.

## Compare two XLSX versions

Use this before an update when you want to see which dates or historical values changed. The app does not decide which file is newer: you choose that order.

1. Select the **newer** XLSX as the normal import file and choose **Open and preview file**. Set the worksheet, header/start rows, date column, selected instruments, declared units/roles, parsing conventions and current cutoff; a saved import profile can restore the layout.
2. Inspect the preview and set blank-skipping or cached-formula permissions explicitly if appropriate. The exact same configuration and permissions will validate both workbooks. Formula caches are not recalculated and may be stale. Every selected instrument needs at least one included observation in each file; an empty selected series rejects the comparison.
3. Under **Compare two Excel versions**, select the **older** XLSX using **Older Excel workbook**, then choose **Compare with older workbook**. Its selected worksheet name and date/value headers must match at the same physical columns. A mismatch requires manual correction; it is not silently remapped. Invalid selected input in either file rejects the result, including duplicates or malformed rows after the cutoff.
4. Review the per-instrument older/newer counts and first/last dates. **New** means a date only in the newer validated records; **corrected** means a shared date with a different parsed value; **absent in newer** means a date only in the older validated records; **unchanged** means a shared date with the same value.
5. Use **Previous changes** and **Next changes** (100 changed observations per page) to inspect every changed date, its older/newer values and difference in declared units (**newer minus older**, not percent). Missing sides have no difference. Equality uses unrounded parsed values, so a small correction can count even if ordinary commodity or FX tables would round both values alike. Blank and future omissions are reported separately.
6. If you want to analyze the newer workbook, choose **Validate selected instruments**, inspect its import review and then **Add validated instruments to this tab**. Comparing alone never adds observations. Changing the file, mapping or comparison selection invalidates the old comparison.

For example, older dates Jan1=100, Jan2=110, Jan4=130 and newer dates Jan1=105, Jan3=120, Jan4=130 yield one correction (+5 on Jan1), one new date (Jan3), one absent date (Jan2) and one unchanged date (Jan4). Each file has three selected observations. These are invented values.

An absent date is not proof that somebody deleted a quote or that a market was closed. It can reflect shorter coverage or explicit blank/cutoff omissions. Check the counts, ranges, omissions and selected configuration before interpreting the result. A comparison does not verify source rights, settlement definitions or contract continuation rules.

Both files and the comparison stay in tab memory and disappear on reload. Nothing is uploaded, merged, written to SQLite or saved automatically. Comparison export and CSV comparison are not provided. Existing selected-series and report exports remain separate features and are not a saved comparison.

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
