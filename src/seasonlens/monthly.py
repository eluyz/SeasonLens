"""Monthly arithmetic means and observation counts for prepared daily data."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_complex_dtype,
    is_datetime64_any_dtype,
    is_float_dtype,
    is_numeric_dtype,
)


@dataclass(frozen=True)
class MonthlyResult:
    """Year-by-month tables; absent months have NaN means and zero counts."""

    means: pd.DataFrame
    counts: pd.DataFrame


def aggregate_monthly(
    frame: pd.DataFrame,
    *,
    date_column: str = "date",
    value_column: str = "value",
) -> MonthlyResult:
    """Aggregate a prepared daily series without changing the input.

    Dates must already have a timezone-naive pandas datetime dtype and be at
    midnight. Values must have a real numeric dtype and be finite. Missing
    values, duplicate dates and duplicate column labels are rejected rather
    than silently repaired. Zero and negative values are valid observations.

    Both returned tables contain every year from the first observation to the
    last and all twelve calendar months. Each monthly mean weights individual
    observations equally; this function does not fill or interpolate gaps.
    Extremely large finite values can overflow pandas' arithmetic aggregation;
    these groups raise ValueError instead of returning a nonfinite mean.
    Floating-point dtypes wider than 64 bits are unsupported.

    Raises:
        ValueError: The input does not meet the prepared-series requirements.
    """
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("frame must be a pandas DataFrame.")
    if frame.columns.has_duplicates:
        raise ValueError("Column names must be unique.")
    if (
        not isinstance(date_column, str)
        or not date_column
        or not isinstance(value_column, str)
        or not value_column
    ):
        raise ValueError("date_column and value_column must be nonempty strings.")
    if date_column == value_column:
        raise ValueError("date_column and value_column must be different.")
    for column in (date_column, value_column):
        if column not in frame.columns:
            raise ValueError(f"Required column {column!r} is missing.")
    if frame.empty:
        raise ValueError("At least one observation is required.")

    dates = frame[date_column]
    values = frame[value_column]
    if not is_datetime64_any_dtype(dates.dtype):
        raise ValueError("Dates must already have a pandas datetime dtype.")
    if isinstance(dates.dtype, pd.DatetimeTZDtype):
        raise ValueError("Dates must be timezone-naive.")
    if dates.isna().any():
        raise ValueError("Dates must not contain missing values.")
    if not dates.eq(dates.dt.normalize()).all():
        raise ValueError("Dates must be daily observations at midnight.")
    if dates.duplicated().any():
        raise ValueError("Duplicate dates are not allowed.")

    if (
        not is_numeric_dtype(values.dtype)
        or is_bool_dtype(values.dtype)
        or is_complex_dtype(values.dtype)
    ):
        raise ValueError("Values must have a real numeric dtype (not boolean or complex).")
    if is_float_dtype(values.dtype) and values.dtype.itemsize > 8:
        raise ValueError("Floating-point values must use a supported dtype of up to 64 bits.")
    if values.isna().any():
        raise ValueError("Values must not contain missing values.")
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Values must be finite.")

    # A fresh frame avoids mutating the caller and avoids alignment on a
    # possibly duplicated or nondefault input index.
    prepared = pd.DataFrame(
        {
            "year": dates.dt.year.to_numpy(),
            "month": dates.dt.month.to_numpy(),
            "value": values.to_numpy(),
        }
    )
    grouped = prepared.groupby(["year", "month"])["value"].agg(["mean", "count"])
    if not np.isfinite(grouped["mean"].to_numpy()).all():
        raise ValueError(
            "Monthly aggregation exceeded the supported numeric range (overflow); "
            "rescale the values before calculating means."
        )
    years = pd.Index(
        range(int(prepared["year"].min()), int(prepared["year"].max()) + 1),
        name="year",
    )
    months = pd.Index(range(1, 13), name="month")
    means = grouped["mean"].unstack("month").reindex(index=years, columns=months)
    counts = grouped["count"].unstack("month").reindex(index=years, columns=months)
    return MonthlyResult(means=means.astype("float64"), counts=counts.fillna(0).astype("int64"))
