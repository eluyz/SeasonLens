# Price-list comparison demonstration

Public instructions: [English](https://eluyz.github.io/SeasonLens/demo/) and [Polski](https://eluyz.github.io/SeasonLens/demo/pl.html). This directory contains static instructions and two invented XLSX examples, served directly by GitHub Pages. No script, upload form, provider request or telemetry is added to the guide.

## Expected result

Open `seasonlens-newer.xlsx` first, select `Prices`, header1, start4, dateA, priceB, EUR/t, wheat role, ISO text dates, decimal dot, cutoff2026-10-07. Both consent boxes stay off. Compare against `seasonlens-older.xlsx`.

The older file has210 rows, 2025-12-17–2026-10-06; the newer has210 rows, 2025-12-18–2026-10-07. Expected counts: new1, corrected1, absent1, unchanged208. Changes: absent2025-12-17=210; correction2026-10-06,213.29→218.29,difference5; new2026-10-07=215. No blanks/formulas/future-row omissions. Row3 (2026-10-08=999) is outside the selected physical row range in both files.

Only a separate Validate and Add action installs the newer series. Six built-in samples then become seven options; private Wheat sample in EUR/t ends at215 on2026-10-07. Report export is an optional analysis snapshot, not a comparison export. Timing is a presentation plan, not a measured usability result.

## Rebuild the files

`examples/create_comparison_demo.mjs` creates both workbooks using `@oai/artifact-tool`, following the same explicit synthetic wheat construction as `examples/create_import_template.mjs`. No input/provider file is read. In a temporary Node workspace that resolves this authoring dependency, run the builder with an output directory. Normalize each generated XLSX using `python examples/normalize_template_package.py <xlsx>`, then copy only the two `.xlsx` files here. Preview images and inspect logs are authoring checks, not public deliverables. Export timestamps/ZIP metadata may differ between builds; validate cell content and the expected comparison, not a reproducibility claim about binary hashes.

The ordinary public-page builder leaves this directory intact. The immutable v0.1.3 browser ZIP is unchanged and does not contain this later example pair. A future source distribution includes the guide and files through `MANIFEST.in`; no package version or previous release is changed by this documentation update.
