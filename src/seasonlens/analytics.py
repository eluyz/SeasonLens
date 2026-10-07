"""Local, auditable analytics on prepared daily observations.

All dates are explicit; these functions neither fetch data nor write files.
Observation counts are not certificates of trading-session completeness.
"""

from calendar import monthrange
from dataclasses import dataclass, replace
from datetime import date, datetime
from numbers import Integral

import numpy as np
import pandas as pd

from .monthly import aggregate_monthly
from .seasonal import SeasonalResult, analyze_seasonality


@dataclass(frozen=True)
class MovingAverageResult:
    as_of: date
    frame: pd.DataFrame
    excluded_future_observations: int


@dataclass(frozen=True)
class MonthlyReturnResult:
    as_of: date
    frame: pd.DataFrame
    excluded_future_observations: int


@dataclass(frozen=True)
class NormalizedSeasonalResult:
    seasonal: SeasonalResult
    yearly_monthly: pd.DataFrame
    yearly_counts: pd.DataFrame
    bases: pd.DataFrame


@dataclass(frozen=True)
class PartialMonthResult:
    as_of: date
    window_years: int
    start_year: int
    end_year: int
    years: pd.DataFrame
    baseline_mean: float
    baseline_minimum: float
    baseline_maximum: float
    year_count: int
    observation_count: int
    current_mean: float
    current_observation_count: int
    difference: float
    excluded_future_observations: int


@dataclass(frozen=True)
class CurrencyConversionResult:
    as_of: date
    frame: pd.DataFrame
    unmatched_price_observations: int
    unmatched_fx_observations: int
    excluded_future_price_observations: int
    excluded_future_fx_observations: int


def _cutoff(as_of):
    if not isinstance(as_of, date) or isinstance(as_of, datetime):
        raise ValueError("as_of must be a datetime.date without a time.")


def _prepared(frame, date_column, value_column):
    # Reuse the complete strict contract, including excluded-row validation and
    # numeric-range limitations, rather than silently accepting repaired input.
    aggregate_monthly(frame, date_column=date_column, value_column=value_column)
    result = frame[[date_column, value_column]].copy(deep=True)
    result.columns = ["date", "value"]
    result["value"] = result["value"].astype("float64")
    return result.sort_values("date", kind="stable").reset_index(drop=True)


def _visible(prepared, as_of):
    mask = prepared["date"].dt.date <= as_of
    return prepared.loc[mask].copy(), int((~mask).sum())


def _positive(prepared, purpose):
    if prepared["value"].le(0).any():
        raise ValueError(f"{purpose} requires strictly positive values, including excluded rows.")


def _finite(values, purpose):
    if not np.isfinite(np.asarray(values, dtype="float64")).all():
        raise ValueError(f"{purpose} exceeded the supported numeric range (overflow).")


def _window(as_of, window_years):
    if (not isinstance(window_years, Integral)
            or isinstance(window_years, (bool, np.bool_)) or window_years <= 0):
        raise ValueError("window_years must be a positive integer.")
    start = as_of.year - int(window_years)
    if start < 1:
        raise ValueError("The historical window must start at calendar year 1 or later.")
    return int(window_years), start, as_of.year - 1


def moving_averages(frame, *, as_of: date, date_column="date", value_column="value") -> MovingAverageResult:
    """Return observation-based SMA20/SMA50, with an inclusive explicit cutoff.

Rows are sorted by date. SMA20 at observation k is the arithmetic mean of
observations k-19..k, not 20 calendar days. It is missing until 20 observations
exist; SMA50 analogously requires 50. Gaps are not filled and zero/negative
levels are allowed. Full-input validation precedes exclusion of future rows.
"""
    _cutoff(as_of)
    prepared = _prepared(frame, date_column, value_column)
    visible, excluded = _visible(prepared, as_of)
    result = visible.reset_index(drop=True)
    for window in (20, 50):
        result[f"sma{window}"] = result["value"].rolling(window, min_periods=window).mean()
        _finite(result[f"sma{window}"].iloc[window - 1:], f"SMA{window}")
    return MovingAverageResult(as_of, result, excluded)


def monthly_returns(frame, *, as_of: date, date_column="date", value_column="value") -> MonthlyReturnResult:
    """Return close-to-close percent changes for consecutive calendar months.

Close means the last observed value in a calendar month, not a certified
exchange settlement or last trading-session price. Return =
100 * (this_month_close / immediately_previous_calendar_month_close - 1).
A missing calendar month breaks the comparison; it is never skipped over.
All original prices must be positive. The month grid extends from the first
visible observation through the cutoff month (cutoff month alone if none are
visible). Calendar status and actual last-observation dates expose partial or
stale input; no session calendar is inferred.
"""
    _cutoff(as_of)
    prepared = _prepared(frame, date_column, value_column)
    _positive(prepared, "Monthly returns")
    visible, excluded = _visible(prepared, as_of)
    start = pd.Period(as_of, freq="M") if visible.empty else visible["date"].iloc[0].to_period("M")
    months = pd.period_range(start, pd.Period(as_of, freq="M"), freq="M", name="month")
    result = pd.DataFrame(index=months)
    if visible.empty:
        result["close"] = np.nan
        result["last_observation_date"] = pd.NaT
        result["observation_count"] = 0
    else:
        groups = visible.groupby(visible["date"].dt.to_period("M"))
        result["close"] = groups["value"].last().reindex(months)
        result["last_observation_date"] = groups["date"].last().reindex(months)
        result["observation_count"] = groups["value"].count().reindex(months).fillna(0).astype("int64")
    result["previous_close"] = result["close"].shift(1)
    comparable = result["close"].notna() & result["previous_close"].notna()
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        result["return_pct"] = (result["close"] / result["previous_close"] - 1) * 100
    _finite(result.loc[comparable, "return_pct"], "Monthly return")
    cutoff_ended = as_of.day == monthrange(as_of.year, as_of.month)[1]
    result["calendar_status"] = [
        "month_in_progress" if month == months[-1] and not cutoff_ended else "month_ended"
        for month in months
    ]
    return MonthlyReturnResult(as_of, result, excluded)


def normalized_seasonality(frame, *, as_of: date, window_years: int,
                          date_column="date", value_column="value") -> NormalizedSeasonalResult:
    """Index each year's observed path to 100 at its first observed price.

Every original price must be positive. For each visible calendar year,
indexed_value = 100 * price / first_observed_price_in_that_year. No January-1
observation is invented: base_date/base_value are explicit. Monthly path
points are means of that year's indexed observations, not monthly returns.
The nested SeasonalResult averages yearly monthly points equally in exactly
the N years before as_of.year and exposes reference-year partial status.
Missing base years stay visible in bases and the year/month grids. A partial
reference month is compared with historical full months, as in SL-004.
"""
    _cutoff(as_of)
    window_years, start, end = _window(as_of, window_years)
    prepared = _prepared(frame, date_column, value_column)
    _positive(prepared, "Year normalization")
    visible, excluded = _visible(prepared, as_of)
    years = pd.Index(range(start, as_of.year + 1), name="year")
    months = pd.Index(range(1, 13), name="month")
    bases = pd.DataFrame(index=years)
    if visible.empty:
        bases["base_date"] = pd.NaT
        bases["base_value"] = np.nan
        nested = analyze_seasonality(prepared, as_of=as_of, window_years=window_years)
        yearly = pd.DataFrame(np.nan, index=years, columns=months)
        counts = pd.DataFrame(0, index=years, columns=months, dtype="int64")
    else:
        groups = visible.groupby(visible["date"].dt.year)
        bases["base_date"] = groups["date"].first().reindex(years)
        bases["base_value"] = groups["value"].first().reindex(years)
        denominators = groups["value"].transform("first")
        indexed = visible.copy()
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            indexed["value"] = (indexed["value"] / denominators) * 100
        _finite(indexed["value"], "Year normalization")
        nested = analyze_seasonality(indexed, as_of=as_of, window_years=window_years)
        nested = replace(nested, excluded_future_observations=excluded)
        monthly = aggregate_monthly(indexed)
        yearly = monthly.means.reindex(index=years, columns=months)
        counts = monthly.counts.reindex(index=years, columns=months).fillna(0).astype("int64")
    return NormalizedSeasonalResult(nested, yearly, counts, bases)


def partial_month_comparison(frame, *, as_of: date, window_years: int,
                             date_column="date", value_column="value") -> PartialMonthResult:
    """Compare the cutoff month's mean through the same day in prior years.

Use exactly as_of.year-N..as_of.year-1. For every baseline year, select only
as_of.month and calendar days 1..as_of.day inclusive; February 29 clamps to
February 28 in non-leap years. Daily counts need not match and no session
calendar is implied. Available yearly means receive equal weight; min/max
are extrema of those yearly means. Empty years stay in the years table with
missing mean and count zero; older years never replace them. Difference is
current partial-month mean minus baseline mean, in original input units.
"""
    _cutoff(as_of)
    window_years, start, end = _window(as_of, window_years)
    prepared = _prepared(frame, date_column, value_column)
    visible, excluded = _visible(prepared, as_of)
    records = []
    for year in range(start, end + 1):
        through = date(year, as_of.month, min(as_of.day, monthrange(year, as_of.month)[1]))
        rows = visible.loc[(visible["date"].dt.year == year)
                           & (visible["date"].dt.month == as_of.month)
                           & (visible["date"].dt.day <= through.day)]
        mean = float(rows["value"].mean()) if len(rows) else float("nan")
        if len(rows):
            _finite([mean], "Partial-month yearly mean")
        records.append((year, through, mean, len(rows), rows["date"].iloc[-1] if len(rows) else pd.NaT))
    years = pd.DataFrame(records, columns=["year", "through_date", "mean", "observation_count", "last_observation_date"]).set_index("year")
    available = years["mean"].dropna()
    if available.empty:
        mean = minimum = maximum = float("nan")
    else:
        with np.errstate(over="ignore", invalid="ignore"):
            mean = float(available.mean())
        minimum, maximum = float(available.min()), float(available.max())
        _finite([mean, minimum, maximum], "Partial-month baseline")
    current = visible.loc[(visible["date"].dt.year == as_of.year)
                          & (visible["date"].dt.month == as_of.month)]
    current_mean = float(current["value"].mean()) if len(current) else float("nan")
    if len(current):
        _finite([current_mean], "Partial-month current mean")
    with np.errstate(over="ignore", invalid="ignore"):
        difference = current_mean - mean
    if len(current) and len(available):
        _finite([difference], "Partial-month difference")
    return PartialMonthResult(as_of, window_years, start, end, years, mean, minimum, maximum,
                              len(available), int(years["observation_count"].sum()),
                              current_mean, len(current), difference, excluded)


def convert_eur_to_pln(price_frame, fx_frame, *, as_of: date,
                       date_column="date", value_column="value",
                       fx_date_column="date", fx_value_column="value") -> CurrencyConversionResult:
    """Convert EUR/t to PLN/t using exact-date PLN-per-EUR observations.

PLN/t = EUR/t * PLN/EUR. Match the two cutoff-limited series by exact daily
date with a one-to-one inner join. Never forward-fill, backfill or substitute
an adjacent FX date. Price levels may be zero/negative; all original FX rates
must be positive. Counts expose unmatched visible price/FX observations and
future exclusions separately. This is a currency conversion, not a return,
and no exchange close/settlement status is inferred for either input.
"""
    _cutoff(as_of)
    prices = _prepared(price_frame, date_column, value_column)
    fx = _prepared(fx_frame, fx_date_column, fx_value_column)
    _positive(fx, "FX conversion")
    prices, price_future = _visible(prices, as_of)
    fx, fx_future = _visible(fx, as_of)
    joined = prices.rename(columns={"value": "eur_price"}).merge(
        fx.rename(columns={"value": "pln_per_eur"}), on="date", how="inner", validate="one_to_one"
    ).sort_values("date", kind="stable").reset_index(drop=True)
    with np.errstate(over="ignore", invalid="ignore"):
        joined["pln_price"] = joined["eur_price"] * joined["pln_per_eur"]
    _finite(joined["pln_price"], "Currency conversion")
    return CurrencyConversionResult(as_of, joined, len(prices) - len(joined), len(fx) - len(joined),
                                    price_future, fx_future)
