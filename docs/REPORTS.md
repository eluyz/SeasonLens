# Quick controls and local analysis reports

The compact **Analysis options** toolbar stays near the top of the viewport while scrolling. It mirrors the original instrument/unit selectors and shows the selected analysis cutoff. Open it to change instruments or jump to seasonality, historical risk, currency effects, import or report export. Imported instruments appear in both selectors. Table and chart frames support horizontal scrolling and keyboard focus. Escape closes the toolbar options.

## Export a report

1. Select the instrument, display units, chart range and analysis settings.
2. Open **Export report** from either navigation or Analysis options.
3. Choose sections. The default includes the market snapshot, monthly prices, technical chart and historical risk. Return stability, FX variance and forecast comparison are optional.
4. Choose **Build report preview**. Selected statistical panels are calculated even if closed, without opening unrelated panels. The preview is a fixed snapshot of this selection, units, cutoff and settings.
5. Choose **Print / Save PDF**, then use the browser's print dialog to save a PDF where supported. A4 landscape is the default page layout; the dialog may override it. **Download HTML** saves the same snapshot as a self-contained, script-free document that can be reopened offline and printed.
6. Choose **Back to analysis**, or Escape, to return. Rebuild after changing settings or importing new data; existing snapshots do not silently update.

The monthly table retains its full declared calendar window. The five-year chart respects hidden year lines and records enabled/hidden choices. The technical chart reflects the chosen range and line toggles. Statistics preserve coverage, unavailable reasons, legends and explanations. Report sections include only the selected instrument's views, plus its explicitly compatible FX when requested; global cross-market comparison and correlation matrices are omitted.

Separate fundamental context is unchecked by default. Open that panel and select its dataset, commodity, region and marketing year before including it. Its provenance and publication dates remain visible, and it is not automatically matched to the selected futures price.

## Privacy and limits

On narrow screens, preview and downloaded HTML retain readable chart widths and locally scroll wide tables. Scroll frames support keyboard focus. Print styles remove those scrolling limits so the whole result can be paginated.

Report creation, preview and download run in the browser. No report is uploaded, published or saved in browser persistent storage. The downloaded HTML includes selected rendered results and SVG charts, without the original observation arrays or application scripts. It can still contain private prices, calculated results and declared source information; keep private exports private unless sharing is permitted.

The preview and download preserve one immutable snapshot. Switching instruments or settings while a snapshot is being prepared rejects the build. Unavailable calculations remain visibly unavailable. The export does not invent forecasts, fill gaps or change calculations. PDF saving uses the browser's facilities rather than a bundled PDF-generation service; availability and pagination can differ between browsers. Downloaded HTML is the portable fallback.
