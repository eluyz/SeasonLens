"""Five recent calendar-year prices and full-history technical warm-up."""

from dataclasses import dataclass
from datetime import date
import math

import numpy as np
import pandas as pd

from .analytics import _cutoff, _finite, _prepared, _visible
from .monthly import aggregate_monthly


@dataclass(frozen=True)
class TechnicalAnalysisResult:
    as_of: date
    frame: pd.DataFrame
    excluded_future_observations: int


@dataclass(frozen=True)
class RecentYearPricesResult:
    as_of: date
    years: tuple[int, ...]
    monthly_means: pd.DataFrame
    monthly_counts: pd.DataFrame
    mean_series: pd.Series
    year_count: pd.Series
    observation_count: pd.Series
    excluded_future_observations: int


def _population_std(window: np.ndarray) -> float:
    """Centered, scaled population deviation without raw-square cancellation.

    Subtracting a nearby observed anchor first preserves narrow float64 price
    differences. If that subtraction overflows for mixed-sign extremes, scale
    the original observations first. Squared normalized deviations stay bounded.
    """
    with np.errstate(over="ignore", invalid="ignore"):
        centered = window - window[0]
    if np.isfinite(centered).all():
        scale = float(np.max(np.abs(centered)))
        if scale == 0:
            return 0.0
        normalized = centered / scale
    else:
        scale = float(np.max(np.abs(window)))
        normalized = window / scale
    mean = math.fsum(float(value) for value in normalized) / len(normalized)
    variance = math.fsum((float(value) - mean) ** 2 for value in normalized) / len(normalized)
    with np.errstate(over="ignore", invalid="ignore"):
        deviation = scale * math.sqrt(variance)
    _finite([deviation], "Bollinger population deviation")
    return deviation


def technical_analysis(frame: pd.DataFrame, *, as_of: date) -> TechnicalAnalysisResult:
    """Return every visible observation with SMA20/100/200 and Bollinger bounds.

    Technical windows count observations, not calendar or trading days. Full
    history through the inclusive cutoff warms up indicators before a consumer
    selects a trailing display range. SMA columns are missing until 20, 100 or
    200 observations respectively. Bollinger upper/lower = SMA20 +/- two times
    the 20-observation population standard deviation (ddof=0); there is no
    additional middle-band column because SMA20 already serves that purpose.

    The entire original prepared input validates before future-date exclusions.
    Zero/negative levels and calendar gaps are permitted. No filling, parsing,
    implicit cutoff, input mutation or display-range truncation occurs.
    """
    _cutoff(as_of)
    prepared = _prepared(frame, "date", "value")
    visible, excluded = _visible(prepared, as_of)
    result = visible.reset_index(drop=True)
    for window in (20, 100, 200):
        result[f"sma{window}"] = result["value"].rolling(window, min_periods=window).mean()
        _finite(result[f"sma{window}"].iloc[window - 1:], f"SMA{window}")
    deviation = result["value"].rolling(20, min_periods=20).apply(_population_std, raw=True)
    with np.errstate(over="ignore", invalid="ignore"):
        result["bollinger_upper"] = result["sma20"] + 2 * deviation
        result["bollinger_lower"] = result["sma20"] - 2 * deviation
    for column in ("bollinger_upper", "bollinger_lower"):
        _finite(result[column].iloc[19:], "Bollinger bounds")
    return TechnicalAnalysisResult(as_of, result, excluded)


def recent_year_prices(frame: pd.DataFrame, *, as_of: date) -> RecentYearPricesResult:
    """Monthly means for exactly cutoff-year minus four through cutoff-year.

    Unlike completed-year seasonal baselines, this comparison INCLUDES the
    current year. Each available yearly monthly mean contributes equal weight
    to mean_series, irrespective of its observation count. Missing years/months
    remain visible and never extend the five-year window. Future current-year
    months have missing means and zero counts; their comparison mean can still
    use available preceding years, without extrapolating the current-year line.
    Current-month observations are limited by the inclusive cutoff, so its
    point may represent a partial month. Counts do not certify session coverage.
    """
    _cutoff(as_of)
    if as_of.year < 5:
        raise ValueError("The five-year comparison must start at calendar year 1 or later.")
    prepared = _prepared(frame, "date", "value")
    visible, excluded = _visible(prepared, as_of)
    years = tuple(range(as_of.year - 4, as_of.year + 1))
    index = pd.Index(years, name="year")
    months = pd.Index(range(1, 13), name="month")
    if visible.empty:
        means = pd.DataFrame(np.nan, index=index, columns=months)
        counts = pd.DataFrame(0, index=index, columns=months, dtype="int64")
    else:
        monthly = aggregate_monthly(visible)
        means = monthly.means.reindex(index=index, columns=months).copy()
        counts = monthly.counts.reindex(index=index, columns=months).fillna(0).astype("int64")
    year_count = means.count(axis=0).astype("int64").rename("year_count")
    observation_count = counts.sum(axis=0).astype("int64").rename("observation_count")
    with np.errstate(over="ignore", invalid="ignore"):
        mean_series = means.mean(axis=0).rename("mean")
    _finite(mean_series.loc[year_count.gt(0)], "Recent-year comparison mean")
    return RecentYearPricesResult(as_of, years, means, counts, mean_series, year_count, observation_count, excluded)
