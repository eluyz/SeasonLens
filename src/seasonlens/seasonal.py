"""Equal-year seasonal profiles using an explicit calendar cutoff."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
from numbers import Integral

import numpy as np
import pandas as pd

from .monthly import aggregate_monthly


@dataclass(frozen=True)
class SeasonalResult:
    """Declared baseline window and cutoff-limited current-year comparison."""

    as_of: date
    window_years: int
    start_year: int
    end_year: int
    profile: pd.DataFrame
    current: pd.DataFrame
    excluded_future_observations: int


def analyze_seasonality(
    frame: pd.DataFrame,
    *,
    as_of: date,
    window_years: int,
    date_column: str = "date",
    value_column: str = "value",
) -> SeasonalResult:
    """Compare the cutoff year with exactly the preceding calendar years.

    Each month in the profile gives equal weight to each contributing year's
    monthly mean. Minimum and maximum are across those monthly means, not daily
    observations. Absent years remain absent; the declared window is never
    extended to compensate. Counts describe observations and contributing years,
    without asserting trading-session completeness.

    The entire prepared input is validated by ``aggregate_monthly`` before
    excluding dates after ``as_of`` or selecting the historical window. Invalid
    data cannot escape validation through a cutoff. An empty input rejects;
    empty baseline/current selections yield missing means and zero counts.
    Nonfinite arithmetic results raise ValueError. There is no implicit today,
    date parsing, gap filling, or input mutation.
    """
    if not isinstance(as_of, date) or isinstance(as_of, datetime):
        raise ValueError("as_of must be a datetime.date, not a datetime.")
    if (
        not isinstance(window_years, Integral)
        or isinstance(window_years, (bool, np.bool_))
        or window_years <= 0
    ):
        raise ValueError("window_years must be a positive integer.")
    window_years = int(window_years)
    start_year = as_of.year - window_years
    end_year = as_of.year - 1
    if start_year < 1:
        raise ValueError("The historical window must start at calendar year 1 or later.")

    # Deliberately validates all observations, including rows outside the
    # requested window and beyond the cutoff.
    aggregate_monthly(frame, date_column=date_column, value_column=value_column)
    on_or_before = frame[date_column].dt.date <= as_of
    excluded_future = int((~on_or_before).sum())
    visible = frame.loc[on_or_before]
    months = pd.Index(range(1, 13), name="month")
    years = pd.Index(range(start_year, end_year + 1), name="year")
    if visible.empty:
        baseline_means = pd.DataFrame(np.nan, index=years, columns=months)
        baseline_counts = pd.DataFrame(0, index=years, columns=months, dtype="int64")
        current_means = pd.Series(np.nan, index=months, dtype="float64")
        current_counts = pd.Series(0, index=months, dtype="int64")
    else:
        monthly = aggregate_monthly(visible, date_column=date_column, value_column=value_column)
        baseline_means = monthly.means.reindex(index=years, columns=months)
        baseline_counts = monthly.counts.reindex(index=years, columns=months).fillna(0).astype("int64")
        if as_of.year in monthly.means.index:
            current_means = monthly.means.loc[as_of.year].copy()
            current_counts = monthly.counts.loc[as_of.year].copy()
        else:
            current_means = pd.Series(np.nan, index=months, dtype="float64")
            current_counts = pd.Series(0, index=months, dtype="int64")

    year_count = baseline_means.count(axis=0).astype("int64")
    with np.errstate(over="ignore", invalid="ignore"):
        profile = pd.DataFrame(
            {
                "mean": baseline_means.mean(axis=0),
                "minimum": baseline_means.min(axis=0),
                "maximum": baseline_means.max(axis=0),
                "year_count": year_count,
                "observation_count": baseline_counts.sum(axis=0).astype("int64"),
            },
            index=months,
        )
        difference = current_means - profile["mean"]
    for column in ("mean", "minimum", "maximum"):
        observed = year_count.gt(0)
        if not np.isfinite(profile.loc[observed, column].to_numpy()).all():
            raise ValueError("Seasonal profile exceeded the supported numeric range (overflow).")
    comparable = current_means.notna() & profile["mean"].notna()
    if not np.isfinite(difference.loc[comparable].to_numpy()).all():
        raise ValueError("Seasonal difference exceeded the supported numeric range (overflow).")

    cutoff_month_ended = as_of.day == monthrange(as_of.year, as_of.month)[1]
    status = [
        "month_ended"
        if month < as_of.month or (month == as_of.month and cutoff_month_ended)
        else "month_in_progress" if month == as_of.month else "after_cutoff"
        for month in months
    ]
    current = pd.DataFrame(
        {
            "mean": current_means,
            "observation_count": current_counts.astype("int64"),
            "difference": difference,
            "calendar_status": status,
        },
        index=months,
    )
    return SeasonalResult(
        as_of=as_of,
        window_years=window_years,
        start_year=start_year,
        end_year=end_year,
        profile=profile,
        current=current,
        excluded_future_observations=excluded_future,
    )
