# Core contract — SL-001

Status: experimental core implementation specification. Product demand and alternatives research remain open.

API: `aggregate_monthly(frame, *, date_column="date", value_column="value") -> MonthlyResult`.

Input: one nonempty prepared pandas DataFrame, uniquely named columns, distinct selected date/value columns, timezone-naive datetime dtype at midnight, finite real numeric values. Floating-point types above 64 bits are unsupported and explicitly rejected. Boolean and complex values, NaT/NaN, duplicate dates, timezone-aware dates and non-midnight times are rejected. Strings are not parsed by this function. A nonfinite mean from a nonempty group raises ValueError indicating a numeric-range limitation; arbitrary finite magnitudes are not guaranteed to aggregate without overflow.

Output: MonthlyResult.means and MonthlyResult.counts are independent DataFrames with years in ascending order, including all years between the first and last observation; calendar months 1 through 12. Index name is year, column name is month. Missing means are NaN; corresponding counts are integer zero. Data are not silently filled. Input is unchanged.

For each year/month, mean = sum of observed values / observation count. Returned counts measure observations rather than calendar/trading-session completeness.

Independent reference: for dates 2024-01-01 and 2024-01-03 with values 100 and 120, January 2024 has mean 110 and count 2. February has NaN and count 0. If another observation is in 2026, year 2025 remains visible with 12 missing means and 12 zero counts.

Later multi-year profiles will average monthly means with equal weight per year, over exactly the declared calendar-year window. Current-year exclusion, coverage, min/max and reference-year rules are not implemented in SL-001.
