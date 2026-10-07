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
