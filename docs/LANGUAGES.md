# English and Polish

The current browser app offers two language tiles, **English** and **Polski**. English is the default. A selected language is remembered on this device if browser storage is available. Links can select a language explicitly with `?lang=en` or `?lang=pl`.

The preference contains only the language code. It does not save imported files, observations, private instrument names or scenario inputs. Denied storage does not prevent switching languages. Changing the language does not import, clear or recalculate data.

Localization covers interface labels, explanations, table headings, chart legends, validation messages and report text. User-declared names, sources, quote definitions, workbook contents and machine-readable CSV column names retain their supplied form. Dates remain ISO and numerical precision is unchanged.

An exported report retains the language selected when it was built. Changing the interface language does not rewrite an existing report snapshot: rebuild it to obtain a report in the other language. HTML exports remain script-free.

The walkthrough is available in [English](WHEAT_FX_WALKTHROUGH.md) and [Polish](WHEAT_FX_WALKTHROUGH_PL.md), with public pages at `walkthrough.html` and `walkthrough-pl.html`. The historical v0.1.0 download remains the frozen original release; the current website contains subsequent updates.

## Maintaining translations

Edit the curated catalog and bounded message patterns in `src/seasonlens/locale.js`. Preserve formulas, dates, units, coverage limitations and the distinction between historical descriptions and forecasts. Do not translate input values, identifiers or user data by replacing words globally.

The runtime retains original interface text so switching back to English is reversible. Dynamically rendered results are localized after rendering; analytical modules retain their existing definitions. Add checks for new message patterns and test the affected browser flow in both languages.

Terminology feedback is welcome through GitHub Issues. Include the interface section and a public invented example rather than restricted market files.
