# Core contract — SL-001

Status: experimental core implementation specification. Product demand and alternatives research remain open.

API: `aggregate_monthly(frame, *, date_column="date", value_column="value") -> MonthlyResult`.

Input: one nonempty prepared pandas DataFrame, uniquely named columns, distinct selected date/value columns, timezone-naive datetime dtype at midnight, finite real numeric values. Floating-point types above 64 bits are unsupported and explicitly rejected. Boolean and complex values, NaT/NaN, duplicate dates, timezone-aware dates and non-midnight times are rejected. Strings are not parsed by this function. A nonfinite mean from a nonempty group raises ValueError indicating a numeric-range limitation; arbitrary finite magnitudes are not guaranteed to aggregate without overflow.

Output: MonthlyResult.means and MonthlyResult.counts are independent DataFrames with years in ascending order, including all years between the first and last observation; calendar months 1 through 12. Index name is year, column name is month. Missing means are NaN; corresponding counts are integer zero. Data are not silently filled. Input is unchanged.

For each year/month, mean = sum of observed values / observation count. Returned counts measure observations rather than calendar/trading-session completeness.

Independent reference: for dates 2024-01-01 and 2024-01-03 with values 100 and 120, January 2024 has mean 110 and count 2. February has NaN and count 0. If another observation is in 2026, year 2025 remains visible with 12 missing means and 12 zero counts.

Later multi-year profiles will average monthly means with equal weight per year, over exactly the declared calendar-year window. Current-year exclusion, coverage, min/max and reference-year rules are not implemented in SL-001.

## Quality inspection — SL-002

`inspect_series(frame, *, source_rows=None) -> QualityReport` inspects prepared `date`/`value` columns without mutation or repair. Reports contain a total input-row count and frozen `(row, code, message)` issues. Default row labels are one-based data positions; custom positive integer row labels must match input length. Structural issues use `row=None`. Missing values, invalid types, nonfinite numbers, missing/non-midnight/timezone dates and all duplicate-date members are visible. Calendar gaps alone are not errors. No trading calendar or roll correction is assumed.

## CSV preparation — SL-003

`import_csv(path, *, date_column, value_column, date_format, delimiter=",", decimal=".", instrument_column=None, instrument=None, missing_values="reject", max_date=None, skip_rows=0, encoding="utf-8-sig") -> CSVImportResult`.

The explicit date format must specify a four-digit year, month and day; timezone directives are unsupported. Headers/filter values match exactly. A standard `instrument_id` header requires explicit instrument selection. For other identifier conventions, the caller supplies the filter or declares the input a single series. The supported dialect is Python csv.reader strict mode with doubled quote escaping, not a full RFC-conformance validator. Detected CSV structural errors anywhere are fatal. An exact instrument filter ignores other instruments' measure content but records their physical line starts. Selected rows are parsed and inspected before any missing-value or cutoff omissions. Only empty/whitespace numeric cells are skippable; malformed dates/numbers, infinity, literal NaN and duplicate dates remain fatal. Thousands separators are unsupported. Blank numeric cells reject by default. Explicit `missing_values="skip"` retains their original source lines in a separate tuple. `max_date` must be a `datetime.date`; later valid rows are excluded explicitly and recorded. A blank value beyond the cutoff still requires the selected missing-value policy; duplicate or malformed later rows still reject.

The result contains an independent chronological `frame` with exactly `date`/`value`, `report` for selected input before omissions, sorted matching `source_rows`, and disjoint `skipped_missing_rows`, `filtered_instrument_rows`, `filtered_date_rows`. An empty result always rejects. `CSVImportError` subclasses ValueError and exposes the report. Successful output is suitable for SL-001; potential aggregation overflow remains an SL-001 error. No implicit fill, interpolation, duplicate repair, date cutoff, file write or provider call occurs.

Independent reference: synthetic input with Jan 1 value 100, Jan 2 blank and Jan 3 value 120 rejects by default. With explicit blank skipping, January mean is 110/count 2 and the Jan 2 physical line is recorded. A Jan 1 duplicate with a blank still rejects.

## Equal-year profiles — SL-004

`analyze_seasonality(frame, *, as_of, window_years, date_column="date", value_column="value") -> SeasonalResult`.

`as_of` is an explicit `datetime.date` without time; `window_years` is a positive integer (not boolean) and the declared start must be at least year 1. Validate the entire prepared input under SL-001 before any date/window omissions, including monthly arithmetic-range errors outside the requested window. Empty original input rejects; empty selected baseline or reference-year subsets are valid missing results. No parsing, implicit today, mutation, extension to available years, filling or trading calendar occurs.

Baseline start = as_of.year - window_years; end = as_of.year - 1. For every calendar month 1–12, `profile` contains `mean`, `minimum`, `maximum`, `year_count`, `observation_count`. The three statistics operate on the available monthly mean from each year in exactly that window, giving each year equal weight. Extrema are not daily extrema. Counts are integer contributor years and the total number of observed daily values (sum of monthly observation counts). With no contributing year, all three statistics are NaN and both counts are zero. The calendar years are completed before the reference year, but their data can be incomplete.

`current` contains every month 1–12 with `mean`, `observation_count`, `difference`, `calendar_status`. Use only reference-year observations whose dates are on or before as_of; absent mean/difference = NaN, count = zero. Difference = current mean minus profile mean when both exist. `month_ended` means a month before the cutoff month or the cutoff month on its last calendar day (including leap February); `month_in_progress` means an earlier day in the cutoff month; `after_cutoff` means a later month. Status describes the calendar regardless of available observations. Partial reference months are compared with historical full-calendar-month means, not matched day counts.

SeasonalResult also records as_of, window_years, start_year, end_year and the count of valid original observations after the cutoff. DataFrames are independent of input and each other. Nonfinite statistics or differences for observed groups raise ValueError rather than silently representing overflow as missing data. Arbitrary finite magnitudes remain subject to SL-001 and seasonal arithmetic limits.

Independent reference: Jan 2024 values 100,120 -> mean110; Jan 2025 value200 -> mean200. At 2026-01-15 with window5, Jan profile mean155/min110/max200, contributor2/5 and obs3. Current155 at cutoff gives difference0; a Jan16 value999 is excluded and counted, not included in current or baseline. Missing older years do not move the 2021–2025 window.

## Local HTML report — partial SL-005

`render_seasonal_report(results, *, title="SeasonLens — local seasonal analysis", unit="Original input units", import_summary=None) -> str` consumes compatible SeasonalResults for distinct windows and the same reference date/current source series. The optional summary maps text labels to nonnegative integer counts. It returns a standalone escaped HTML document with inline SVG, no external assets/network requests, one chart and 12-row coverage table per window. Labels are English. Values display 12 significant digits. Blue is equal-year baseline, pale blue is the historical range of yearly monthly means, orange is reference-year mean; in-progress markers are hollow. Missing months split lines/ranges rather than bridge gaps. The axis includes zero. Scope is historical input-unit levels, not forecasts, normalized returns or inflation/roll adjustments.

The CSV command-line example selects one instrument and requires an explicit as_of date. It imports/validates before excluding future dates in SL-004, records blank/instrument/future exclusions, and refuses to overwrite either the input (including resolved aliases) or an existing report. Default outputs/ is ignored by git. Restricted inputs produce restricted outputs. CSV export and graphical file selection remain unimplemented.
