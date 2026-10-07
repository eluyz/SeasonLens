"""Private, standalone multi-series explorer; all calculations run in Python."""
from datetime import date, timedelta
from html import escape
import json
import math
import re
import pandas as pd

from .analytics import (moving_averages, monthly_returns, normalized_seasonality,
                        partial_month_comparison, convert_eur_to_pln)
from .monthly import aggregate_monthly
from .seasonal import analyze_seasonality
from .report import render_seasonal_report, _axis


def _sections(document):
    return ''.join(re.findall(r'<section>.*?</section>', document, re.S))


def _records(frame):
    rows = []
    for row in frame.to_dict('records'):
        rows.append({k: (v.isoformat()[:10] if hasattr(v, 'isoformat') else
                         None if isinstance(v, float) and math.isnan(v) else v)
                     for k, v in row.items()})
    return rows


def _fmt(value):
    return 'Missing' if value is None or math.isnan(float(value)) else format(float(value), '.6g')


def _heatmap(frame):
    frame = frame.copy()
    frame['year'] = frame.index.year
    frame['month'] = frame.index.month
    rows = []
    for year, group in frame.groupby('year'):
        cells = []
        for month in range(1, 13):
            item = group[group['month'] == month]
            if item.empty:
                cells.append('<td class="missing">Missing</td>')
                continue
            r = item.iloc[0]
            value = float(r['return_pct'])
            color = '#f1f5f9' if math.isnan(value) else '#d1fae5' if value > 0 else '#ede9fe' if value < 0 else '#fff'
            partial = r['calendar_status'] == 'month_in_progress'
            label = _fmt(value) + ('%' if math.isfinite(value) else '') + (' *' if partial else '')
            cells.append(f'<td style="background:{color}" title="Last observed price date: {escape(str(r["last_observation_date"]))}">{label}</td>')
        rows.append(f'<tr><th>{int(year)}</th>'+''.join(cells)+'</tr>')
    return '<div class="table-wrap"><table><thead><tr><th>Year</th>'+''.join(f'<th>{m}</th>' for m in ('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'))+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def _view(frame, *, as_of, unit):
    daily = moving_averages(frame, as_of=as_of)
    axes = {}
    for horizon in ('90', '365', 'all'):
        visible = daily.frame if horizon == 'all' else daily.frame[daily.frame.date.dt.date >= as_of-timedelta(days=int(horizon))]
        for mask in range(1,8):
            columns = [name for i,name in enumerate(('value','sma20','sma50')) if mask & (1 << i)]
            values = [float(v) for name in columns for v in visible[name] if not math.isnan(float(v))]
            axes[horizon+':'+str(mask)] = _axis(values) if values else None
    profiles = [analyze_seasonality(frame, as_of=as_of, window_years=n) for n in (5, 10)]
    normalized = []
    bases = []
    for n in (5, 10):
        try:
            indexed = normalized_seasonality(frame, as_of=as_of, window_years=n)
            normalized.append(indexed.seasonal)
            bases.append(f'<details><summary>{n}-year normalization bases</summary><div class="table-wrap">'+indexed.bases.to_html(escape=True,na_rep='Missing',border=0)+'</div></details>')
        except ValueError as exc:
            normalization_error = str(exc)
            break
    else:
        normalization_error = None
    try:
        returns = _heatmap(monthly_returns(frame, as_of=as_of).frame)
    except ValueError as exc:
        returns = '<p>Monthly returns unavailable: '+escape(str(exc))+'</p>'
    partial_rows = []
    for n in (5, 10):
        p = partial_month_comparison(frame, as_of=as_of, window_years=n)
        partial_rows.append('<tr>'+''.join(f'<td>{escape(str(v))}</td>' for v in
                            (n, _fmt(p.baseline_mean), _fmt(p.current_mean), _fmt(p.difference), p.year_count, p.observation_count, p.current_observation_count))+'</tr>')
    selected = frame[frame.date.dt.date <= as_of].sort_values('date')
    last = selected.date.iloc[-1].date() if len(selected) else None
    if len(selected):
        observed_months = set(selected.date.dt.to_period('M'))
        calendar_months = pd.period_range(selected.date.iloc[0].to_period('M'),pd.Period(as_of,freq='M'),freq='M')
        missing_months = sum(month not in observed_months for month in calendar_months)
    else:
        missing_months = None
    return dict(daily=_records(daily.frame), axes=axes, profiles=_sections(render_seasonal_report(profiles, unit=unit)),
                normalized=('<p>Normalized view unavailable: '+escape(normalization_error)+'</p>' if normalization_error else
                            _sections(render_seasonal_report(normalized, unit='Index: first observed value of each year = 100'))+''.join(bases)),
                heatmap=returns, partial=''.join(partial_rows), unit=unit,
                observations=len(selected), last_date=last.isoformat() if last else 'Missing',
                age_days=(as_of-last).days if last else None,
                future_excluded=daily.excluded_future_observations,
                missing_months=missing_months)


def render_empty_dashboard(*, as_of):
    """Local import screen for an initialized database with no observations."""
    if type(as_of) is not date:
        raise ValueError('An explicit date is required.')
    template = (__import__('pathlib').Path(__file__).with_name('dashboard.html')).read_text(encoding='utf-8')
    return template.replace('@@TITLE@@','SeasonLens — import your first CSV').replace('@@ASOF@@',as_of.isoformat()).replace('@@DATA@@','{}').replace('@@LOCAL@@','true')


def render_dashboard(series, *, as_of, title='SeasonLens', local_import=False):
    """series is a mapping of ID to frame/title/unit/quote_semantics/source.

    The output embeds observations and derived results. Keep it private for
    restricted inputs. EUR/t conversion joins exact dates, without carry-forward.
    """
    if not isinstance(as_of, date) or type(as_of) is not date or not series:
        raise ValueError('An explicit date and at least one series are required.')
    payload = {}
    for identifier, entry in series.items():
        unit = entry.get('unit', 'Input units')
        data = _view(entry['frame'], as_of=as_of, unit=unit)
        views = {'Original': data}
        if unit == 'EUR/t' and 'EUR_PLN' in series and series['EUR_PLN'].get('unit') == 'PLN per EUR' and series['EUR_PLN'].get('source') in ('ECB_REFERENCE', 'SYNTHETIC'):
            conversion = convert_eur_to_pln(entry['frame'], series['EUR_PLN']['frame'], as_of=as_of)
            if len(conversion.frame):
                converted = conversion.frame[['date', 'pln_price']].rename(columns={'pln_price':'value'})
                views['PLN/t'] = _view(converted, as_of=as_of, unit='PLN/t')
                origin = 'invented synthetic EUR/PLN values' if series['EUR_PLN'].get('source') == 'SYNTHETIC' else 'ECB EUR/PLN reference rates'
                views['PLN/t']['conversion_note'] = f'Exact-date conversion using {origin}. Unmatched price dates: {conversion.unmatched_price_observations}. This is not an executable PLN quote.'
        elif unit == 'EUR/t':
            data['conversion_note'] = 'PLN conversion requires a separately identified ECB EUR/PLN reference series with units PLN per EUR.'
        payload[str(identifier)] = dict(title=entry.get('title', str(identifier)), unit=unit,
                                       semantics=entry.get('quote_semantics', 'User-defined observations'),
                                       source=entry.get('source', 'User import'), views=views)
    encoded = json.dumps(payload, allow_nan=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&','\\u0026')
    template = (__import__('pathlib').Path(__file__).with_name('dashboard.html')).read_text(encoding='utf-8')
    return template.replace('@@TITLE@@', escape(title)).replace('@@ASOF@@', as_of.isoformat()).replace('@@DATA@@', encoded).replace('@@LOCAL@@', 'true' if local_import else 'false')
