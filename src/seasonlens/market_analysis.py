"""Auditable market comparisons on strict prepared observations.

Outputs are JSON-native: unavailable statistics are None, never NaN. Windows
count observed intervals, not a certified trading calendar. No filling, network,
implicit today, investment-return or exchange-close assumption is made.
"""

from calendar import monthrange
from datetime import date, datetime
from numbers import Integral, Real
import math

import numpy as np
import pandas as pd

from .analytics import _cutoff, _finite, _prepared, _visible, _window
from .monthly import aggregate_monthly


def _iso(value):
    return value.date().isoformat() if isinstance(value, pd.Timestamp) else value.isoformat()


def _shift_months(day, months):
    ordinal = day.year * 12 + day.month - 1 - months
    year, month = divmod(ordinal, 12)
    if year < 1:
        return date(1, 1, 1)
    return date(year, month + 1, min(day.day, monthrange(year, month + 1)[1]))


def _data(frame, as_of):
    _cutoff(as_of)
    return _visible(_prepared(frame, "date", "value"), as_of)


def _number(value, purpose):
    result = float(value)
    _finite([result], purpose)
    return result


def _difference(end, start, purpose):
    return _number(end - start, purpose)


def _pct(end, start):
    if start <= 0 or end <= 0:
        return None
    return _number((end / start - 1) * 100, "Percentage change")


def market_snapshot(frame, *, as_of):
    """Latest level, explicitly dated reference changes and inclusive midranks.

Month/quarter targets are cutoff minus1/3 calendar months; YTD target is prior
December31. Reference is last observed date <=target, with no substitution
from a later date. Historical windows are cutoff minus1/5 calendar years
through cutoff inclusive. Midrank =100*(below +0.5*equal)/N, including latest.
"""
    visible, excluded = _data(frame, as_of)
    latest = None if visible.empty else visible.iloc[-1]
    result = dict(as_of=as_of.isoformat(), last_date=None, last_value=None,
                  observation_count=len(visible), excluded_future_observations=excluded,
                  changes={}, sma200=None, distance_sma200_pct=None, position={})
    targets = {"previous": None, "month": _shift_months(as_of, 1),
               "quarter": _shift_months(as_of, 3),
               "ytd": date(as_of.year - 1, 12, 31) if as_of.year > 1 else None}
    for key, target in targets.items():
        row = dict(target_date=target.isoformat() if target else None,
                   reference_date=None, reference_value=None, change=None, change_pct=None)
        refs = visible.iloc[:-1] if key == "previous" else visible.loc[
            visible["date"].dt.date <= target] if target else visible.iloc[:0]
        if latest is not None and not refs.empty:
            ref = refs.iloc[-1]
            row.update(reference_date=_iso(ref.date), reference_value=float(ref.value),
                       change=_difference(float(latest.value), float(ref.value), "Level change"),
                       change_pct=_pct(float(latest.value), float(ref.value)))
        result["changes"][key] = row
    if latest is not None:
        result.update(last_date=_iso(latest.date), last_value=float(latest.value))
        if len(visible) >= 200:
            sma = _number(visible.value.iloc[-200:].mean(), "SMA200")
            result.update(sma200=sma, distance_sma200_pct=_pct(float(latest.value), sma))
    for label, years in (("one_year", 1), ("five_year", 5)):
        start = _shift_months(as_of, 12 * years)
        rows = visible.loc[visible.date.dt.date >= start]
        result["position"][label] = dict(start_date=start.isoformat(), end_date=as_of.isoformat(),
            minimum=float(rows.value.min()) if len(rows) else None,
            maximum=float(rows.value.max()) if len(rows) else None,
            percentile=float(100 * ((rows.value < latest.value).sum()
                + .5 * (rows.value == latest.value).sum()) / len(rows)) if len(rows) else None,
            observation_count=len(rows))
    return result


def market_indicators(frame, *, as_of):
    """Wilder RSI14 and unannualized sample daily log-change sigma, in percent.

RSI seed is first14 observed differences; recurrence is (13*prior+next)/14.
A flat series yields50, onlygains100, onlylosses0. Volatility20/60 requires
20/60 consecutive observed positive-endpoint intervals; invalid endpoints
make that window unavailable. Earlier visible history warms both measures.
"""
    visible, excluded = _data(frame, as_of)
    values = visible.value.to_numpy(dtype=float)
    n = len(values)
    rsi = [None] * n
    with np.errstate(over="ignore", invalid="ignore"):
        differences = np.diff(values)
    _finite(differences, "RSI differences")
    if n > 14:
        gains = np.maximum(differences, 0)
        losses = np.maximum(-differences, 0)
        # Divide before summing to keep an otherwise finite average finite.
        avg_gain = _number(math.fsum(float(x / 14) for x in gains[:14]), "RSI average gain")
        avg_loss = _number(math.fsum(float(x / 14) for x in losses[:14]), "RSI average loss")
        for i in range(14, n):
            if i > 14:
                avg_gain = _number(avg_gain * (13 / 14) + float(gains[i - 1]) / 14, "RSI gain")
                avg_loss = _number(avg_loss * (13 / 14) + float(losses[i - 1]) / 14, "RSI loss")
            scale = max(avg_gain, avg_loss)
            rsi[i] = 50.0 if scale == 0 else 100 * (avg_gain / scale) / (avg_gain / scale + avg_loss / scale)
    log_changes = np.full(max(n - 1, 0), np.nan)
    good = (values[:-1] > 0) & (values[1:] > 0)
    log_changes[good] = np.log(values[1:][good]) - np.log(values[:-1][good])
    result = dict(dates=[_iso(x) for x in visible.date], rsi14=rsi,
                  excluded_future_observations=excluded)
    for window in (20, 60):
        output = [None] * n
        for i in range(window, n):
            sample = log_changes[i - window:i]
            if np.isfinite(sample).all():
                output[i] = _number(float(np.std(sample, ddof=1)) * 100, "Log-change volatility")
        result[f"volatility{window}"] = output
    return result


def seasonal_distribution(frame, *, as_of, window_years=10):
    """Completed-calendar-year monthly means, equal-year distribution.

Linear-interpolation quartiles operate on available yearly monthly means,
not pooled daily levels. Missing years don't extend the declared window.
No current partial month participates; counts do not imply complete sessions.
"""
    visible, excluded = _data(frame, as_of)
    window_years, start, end = _window(as_of, window_years)
    historical = visible.loc[(visible.date.dt.year >= start) & (visible.date.dt.year <= end)]
    monthly = aggregate_monthly(historical) if len(historical) else None
    output = []
    for month in range(1, 13):
        available = monthly.means[month].dropna() if monthly else pd.Series(dtype=float)
        record = dict(month=month, mean=None, median=None, q25=None, q75=None,
                      year_count=len(available), observation_count=int(monthly.counts[month].sum()) if monthly else 0)
        if len(available):
            record.update(mean=_number(available.mean(), "Seasonal mean"),
                median=_number(available.median(), "Seasonal median"),
                q25=_number(available.quantile(.25), "Seasonal Q25"),
                q75=_number(available.quantile(.75), "Seasonal Q75"))
        output.append(record)
    return dict(start_year=start, end_year=end, window_years=window_years,
                excluded_future_observations=excluded, months=output)


def _mapping(frames, as_of):
    if not isinstance(frames, dict) or not frames or any(not isinstance(k, str) or not k for k in frames):
        raise ValueError("frames must be a nonempty mapping with nonempty string identifiers.")
    return {key: _data(frame, as_of)[0] for key, frame in frames.items()}


def _start(start_date, as_of):
    _cutoff(start_date)
    if start_date > as_of:
        raise ValueError("start_date must not be later than as_of.")


def indexed_comparison(frames, *, as_of, start_date):
    """Base100 at first common observed date on/after start, exact-date join.

Every plotted date is shared by all selected series. No forward-fill; a
nonpositive joined level makes that instrument unavailable for this positive
percentage-index view. Levels remain usable by other analyses.
"""
    _cutoff(as_of)
    _start(start_date, as_of)
    prepared = _mapping(frames, as_of)
    joined = None
    columns = {}
    for index, (key, rows) in enumerate(prepared.items()):
        columns[key] = f"series_{index}"
        part = rows.loc[rows.date.dt.date >= start_date].rename(columns={"value": columns[key]}).set_index("date")
        joined = part if joined is None else joined.join(part, how="inner")
    joined = joined.sort_index()
    result = dict(requested_start_date=start_date.isoformat(), as_of=as_of.isoformat(),
                  base_date=_iso(joined.index[0]) if len(joined) else None,
                  dates=[_iso(x) for x in joined.index], series={}, observation_count=len(joined))
    for key in prepared:
        values = joined[columns[key]].to_numpy(dtype=float)
        available = bool(len(values)) and bool((values > 0).all())
        indexed = values / values[0] * 100 if available else []
        _finite(indexed, "Base100 comparison")
        result["series"][key] = dict(base_value=float(values[0]) if len(values) else None,
                                    values=[float(x) for x in indexed] if available else [None] * len(values))
    return result


def _returns(rows):
    output = []
    records = list(rows.itertuples(index=False))
    for previous, current in zip(records, records[1:]):
        value = _pct(float(current.value), float(previous.value))
        if value is not None:
            output.append((previous.date, current.date, value))
    result = pd.DataFrame(output, columns=["start_date", "date", "return_pct"])
    for key in ("start_date", "date"):
        result[key] = pd.to_datetime(result[key])
    result["return_pct"] = result["return_pct"].astype(float)
    return result


def rolling_correlations(frames, *, as_of, window=60, start_date=None):
    """Pairwise sample correlations of percentage changes with exact intervals.

First compute each series' adjacent observation returns. Join by BOTH start
and end date, so a three-day return never matches a one-day return. A window
contains last N matched intervals; constant samples are unavailable. Any
start-date crop happens after warmup. Common interval counts are explicit.
"""
    if not isinstance(window, Integral) or isinstance(window, (bool, np.bool_)) or window < 2:
        raise ValueError("window must be an integer of at least2.")
    _cutoff(as_of)
    if start_date is not None:
        _start(start_date, as_of)
    prepared = _mapping(frames, as_of)
    returns = {key: _returns(rows) for key, rows in prepared.items()}
    keys = list(prepared)
    pairs = []
    for i, left in enumerate(keys):
        for right in keys[i + 1:]:
            joined = returns[left].merge(returns[right], on=["start_date", "date"], suffixes=("_left", "_right"))
            joined = joined.sort_values("date").reset_index(drop=True)
            records = []
            for j, row in joined.iterrows():
                count = min(j + 1, int(window))
                corr = None
                if count == window:
                    sample = joined.iloc[j - int(window) + 1:j + 1]
                    # Scaling keeps square products in representable range.
                    a = sample.return_pct_left.to_numpy(dtype=float)
                    b = sample.return_pct_right.to_numpy(dtype=float)
                    a = a / max(float(np.max(np.abs(a))), 1)
                    b = b / max(float(np.max(np.abs(b))), 1)
                    a = a - a.mean()
                    b = b - b.mean()
                    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
                    if na > 0 and nb > 0:
                        corr = max(-1.0, min(1.0, _number(float(np.dot(a / na, b / nb)), "Return correlation")))
                if start_date is None or row.date.date() >= start_date:
                    records.append(dict(start_date=_iso(row.start_date), date=_iso(row.date), correlation=corr,
                                        matched_interval_count=count))
            pairs.append(dict(left=left, right=right, window=int(window), observations=records))
    return dict(as_of=as_of.isoformat(), pairs=pairs)


def spread_series(left_frame, right_frame, *, as_of, left_unit, right_unit):
    """Left-minus-right daily levels on exact dates, identical declared units."""
    if not isinstance(left_unit, str) or not left_unit or left_unit != right_unit:
        raise ValueError("Spread requires identical nonempty units.")
    left, lf = _data(left_frame, as_of)
    right, rf = _data(right_frame, as_of)
    joined = left.merge(right, on="date", suffixes=("_left", "_right"))
    values = [_difference(float(row.value_left), float(row.value_right), "Spread") for row in joined.itertuples()]
    return dict(unit=left_unit, dates=[_iso(x) for x in joined.date], values=values,
                observation_count=len(joined), unmatched_left_observations=len(left) - len(joined),
                unmatched_right_observations=len(right) - len(joined),
                excluded_future_left_observations=lf, excluded_future_right_observations=rf)


def pln_attribution(price_frame, fx_frame, *, as_of, start_date=None):
    """Exact additive change in price*FX between dated joint observations.

Default target=cutoff minus1calendar month; explicit start_date is a reference
TARGET, choosing last joint date <=target. End=last joint <=cutoff. Terms are
commodity=(P1-P0)*F0, fx=P0*(F1-F0), interaction=(P1-P0)*(F1-F0).
Percentage points divide each term by positive starting PLN level; they are
unavailable for nonpositive start/end prices. FX must be strictly positive.
"""
    prices, pf = _data(price_frame, as_of)
    fx, ff = _data(fx_frame, as_of)
    original_fx = _prepared(fx_frame, "date", "value")
    if original_fx.value.le(0).any():
        raise ValueError("FX attribution requires strictly positive rates, including excluded rows.")
    target = _shift_months(as_of, 1) if start_date is None else start_date
    _start(target, as_of)
    joined = prices.merge(fx, on="date", suffixes=("_price", "_fx")).sort_values("date")
    result = dict(target_date=target.isoformat(), start_date=None, end_date=None,
                  start_price=None, end_price=None, start_fx=None, end_fx=None,
                  start_pln=None, end_pln=None, commodity=None, fx=None, interaction=None, total=None,
                  commodity_pp=None, fx_pp=None, interaction_pp=None, total_pct=None,
                  matched_observation_count=len(joined), unmatched_price_observations=len(prices)-len(joined),
                  unmatched_fx_observations=len(fx)-len(joined),
                  excluded_future_price_observations=pf, excluded_future_fx_observations=ff)
    refs = joined.loc[joined.date.dt.date <= target]
    if joined.empty or refs.empty:
        return result
    initial, final = refs.iloc[-1], joined.iloc[-1]
    p0, p1 = float(initial.value_price), float(final.value_price)
    f0, f1 = float(initial.value_fx), float(final.value_fx)
    start = _number(p0 * f0, "Starting PLN price")
    end = _number(p1 * f1, "Ending PLN price")
    dp = _difference(p1, p0, "Commodity change")
    df = _difference(f1, f0, "FX change")
    terms = {"commodity": _number(dp*f0, "Commodity attribution"),
             "fx": _number(p0*df, "FX attribution"),
             "interaction": _number(dp*df, "Interaction attribution")}
    result.update(start_date=_iso(initial.date), end_date=_iso(final.date),
                  start_price=p0,end_price=p1,start_fx=f0,end_fx=f1,start_pln=start,end_pln=end,
                  total=_difference(end,start,"PLN price change"), **terms)
    if start > 0 and end > 0:
        for key, value in terms.items():
            result[key+"_pp"] = _number(value/start*100, "Attribution percentage points")
        result["total_pct"] = _number(result["total"]/start*100, "Attribution percentage change")
    return result


def scenario_calculation(*, price, fx, tonnes=1, baseline_price=None, baseline_fx=None):
    """Hypothetical benchmark EUR/t *PLN/EUR *tonnes; no fees/basis/hedges."""
    def numeric(value, label, positive=False):
        if not isinstance(value, Real) or isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{label} must be a finite real number.")
        try:
            converted = float(value)
        except (OverflowError, ValueError) as error:
            raise ValueError(f"{label} must be within the supported numeric range.") from error
        if not math.isfinite(converted):
            raise ValueError(f"{label} must be a finite real number.")
        if positive and value <= 0:
            raise ValueError(f"{label} must be positive.")
        return converted
    price = numeric(price, "price")
    fx = numeric(fx, "fx", True)
    tonnes = numeric(tonnes, "tonnes", True)
    if (baseline_price is None) != (baseline_fx is None):
        raise ValueError("Provide both baseline_price and baseline_fx, or neither.")
    level = _number(price * fx, "Scenario PLN/t")
    result = dict(pln_per_tonne=level, tonnes=tonnes,
                  benchmark_value_pln=_number(level*tonnes,"Scenario benchmark value"),
                  baseline_pln_per_tonne=None, change_pln_per_tonne=None, change_benchmark_value_pln=None,
                  change_pct=None,
                  assumptions="Benchmark price times FX times tonnes; excludes physical basis, fees, taxes, financing and hedges.")
    if baseline_price is not None:
        bp = numeric(baseline_price, "baseline_price")
        bf = numeric(baseline_fx, "baseline_fx", True)
        base = _number(bp*bf,"Baseline PLN/t")
        change = _difference(level,base,"Scenario change")
        result.update(baseline_pln_per_tonne=base,change_pln_per_tonne=change,
                      change_benchmark_value_pln=_number(change*tonnes,"Scenario value change"),
                      change_pct=_pct(level,base))
    return result
