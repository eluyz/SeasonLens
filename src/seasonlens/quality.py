"""Inspect prepared daily observations without repairing or dropping rows."""

from dataclasses import dataclass
from numbers import Integral
from collections.abc import Sequence

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
class QualityIssue:
    """A structural issue or an issue at a source row, without raw values."""

    row: int | None
    code: str
    message: str


@dataclass(frozen=True)
class QualityReport:
    """Inspection results; observation counts do not imply session coverage."""

    total_rows: int
    issues: tuple[QualityIssue, ...]

    @property
    def has_errors(self) -> bool:
        return bool(self.issues)


def inspect_series(
    frame: pd.DataFrame, *, source_rows: Sequence[int] | None = None
) -> QualityReport:
    """Report problems in prepared ``date`` and ``value`` columns.

    The default row labels are one-based data positions, independent of the
    DataFrame index. ``source_rows`` can instead map these to physical CSV line
    starts; an invalid mapping raises ValueError. Data issues are returned in
    the report. This function never parses, fills, drops, or changes input.

    Date values require timezone-naive pandas datetime dtype at midnight.
    Missing values and every member of a duplicate date are reported, including
    duplicates with missing numeric values. Real numeric values are accepted;
    floating dtypes wider than 64 bits, boolean and complex dtypes are rejected.
    No calendar is assumed: absent dates alone are not classified as errors.
    """
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("frame must be a pandas DataFrame.")
    if source_rows is None:
        row_labels = list(range(1, len(frame) + 1))
    else:
        if isinstance(source_rows, (str, bytes)):
            raise ValueError("source_rows must contain positive integer row numbers.")
        try:
            row_labels = list(source_rows)
        except TypeError as exc:
            raise ValueError("source_rows must be a sequence of row numbers.") from exc
        if len(row_labels) != len(frame):
            raise ValueError("source_rows must have one row number per observation.")
        if any(
            not isinstance(row, Integral) or isinstance(row, (bool, np.bool_)) or row <= 0
            for row in row_labels
        ):
            raise ValueError("source_rows must contain positive integer row numbers.")
        row_labels = [int(row) for row in row_labels]

    issues: list[QualityIssue] = []

    def add_rows(mask: pd.Series | np.ndarray, code: str, message: str) -> None:
        for position in np.flatnonzero(np.asarray(mask, dtype=bool)):
            issues.append(QualityIssue(row_labels[position], code, message))

    if frame.empty:
        issues.append(QualityIssue(None, "empty_data", "At least one observation is required."))
    if frame.columns.has_duplicates:
        issues.append(QualityIssue(None, "duplicate_columns", "Column names must be unique."))

    for column, code in (("date", "invalid_date_type"), ("value", "invalid_value_type")):
        occurrences = sum(label == column for label in frame.columns)
        if occurrences != 1:
            issues.append(QualityIssue(None, code, f"Exactly one {column!r} column is required."))

    if sum(label == "date" for label in frame.columns) == 1:
        dates = frame["date"]
        add_rows(dates.isna(), "missing_date", "Date is missing.")
        if not is_datetime64_any_dtype(dates.dtype):
            issues.append(QualityIssue(None, "invalid_date_type", "Dates require a prepared datetime dtype."))
        else:
            if isinstance(dates.dtype, pd.DatetimeTZDtype):
                issues.append(QualityIssue(None, "timezone_date", "Dates must be timezone-naive."))
            non_daily = dates.notna() & (
                dates.dt.hour.ne(0)
                | dates.dt.minute.ne(0)
                | dates.dt.second.ne(0)
                | dates.dt.microsecond.ne(0)
                | dates.dt.nanosecond.ne(0)
            )
            add_rows(non_daily, "non_daily_date", "Date must be at midnight.")
            add_rows(
                dates.notna() & dates.duplicated(keep=False),
                "duplicate_date",
                "Date occurs more than once.",
            )

    if sum(label == "value" for label in frame.columns) == 1:
        values = frame["value"]
        add_rows(values.isna(), "missing_value", "Value is missing.")
        valid_type = (
            is_numeric_dtype(values.dtype)
            and not is_bool_dtype(values.dtype)
            and not is_complex_dtype(values.dtype)
            and not (is_float_dtype(values.dtype) and values.dtype.itemsize > 8)
        )
        if not valid_type:
            issues.append(QualityIssue(None, "invalid_value_type", "Values require a real numeric dtype of up to 64 bits."))
        else:
            # Nullable pandas numeric arrays are converted only after excluding
            # missing cells; those cells retain their own missing_value issues.
            present = values.notna().to_numpy()
            nonfinite = np.zeros(len(values), dtype=bool)
            nonfinite[present] = ~np.isfinite(values.iloc[np.flatnonzero(present)].to_numpy(dtype="float64"))
            add_rows(nonfinite, "nonfinite_value", "Value must be finite.")

    return QualityReport(total_rows=len(frame), issues=tuple(issues))
