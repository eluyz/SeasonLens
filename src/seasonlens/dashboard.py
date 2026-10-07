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
from .comparison import technical_analysis, recent_year_prices

TECHNICAL_COLUMNS = ('value','sma20','sma100','sma200','bollinger_upper','bollinger_lower')


def _monthly_price_matrix(frame, *, as_of, unit):
    """Ten calendar years, colored against the last cutoff-visible daily price."""
    selected = frame[frame.date.dt.date <= as_of].sort_values('date')
    if selected.empty:
        return '<p>No observations through the cutoff. Reference price unavailable.</p>'
    monthly = aggregate_monthly(selected)
    years = tuple(range(max(1, as_of.year - 9), as_of.year + 1))
    means = monthly.means.reindex(index=years, columns=range(1, 13))
    counts = monthly.counts.reindex(index=years, columns=range(1, 13)).fillna(0)
    reference = float(selected.value.iloc[-1])
    reference_date = selected.date.iloc[-1].date().isoformat()
    decimals = 3 if re.fullmatch(r'[A-Z]{3} per [A-Z]{3}', unit) else 0
    rows = []
    for month, name in enumerate(('January','February','March','April','May','June',
                                  'July','August','September','October','November','December'), 1):
        cells = []
        for year in years:
            value = float(means.loc[year, month])
            if math.isnan(value):
                future = year == as_of.year and month > as_of.month
                reason = 'Month after analysis cutoff' if future else 'No historical observations through the cutoff'
                cells.append(f'<td class="{"future-month" if future else "missing"}" title="{reason}">—</td>')
                continue
            relation = 'lower' if value < reference else 'higher' if value > reference else 'equal'
            partial = (year == as_of.year and month == as_of.month
                       and as_of.day != __import__('calendar').monthrange(year, month)[1])
            title = f'Monthly average {relation} than reference; {int(counts.loc[year, month])} observations'
            if partial:
                title += '; current calendar month is partial'
            cells.append(f'<td class="price-{relation}" title="{title}">{value:.{decimals}f}'+(' *' if partial else '')+'</td>')
        rows.append('<tr><th scope="row">'+name+'</th>'+''.join(cells)+'</tr>')
    header = '<tr><th scope="col">Month / Year</th>'+''.join(f'<th scope="col">{year}</th>' for year in years)+'</tr>'
    legend = ('<div class="matrix-key" aria-label="Comparison legend">'
              '<span class="price-higher">Higher monthly average</span>'
              '<span class="price-equal">Equal to reference</span>'
              '<span class="price-lower">Lower monthly average</span>'
              '<span class="missing">— No data / after cutoff</span></div>')
    return ('<div class="price-matrix-layout"><div class="table-wrap"><table class="price-matrix">'
            f'<caption>Monthly average prices · {years[0]}–{years[-1]} · {escape(unit)}</caption>'
            '<thead>'+header+'</thead><tbody>'+''.join(rows)+'</tbody></table></div>'
            '<aside class="matrix-reference"><span>Reference daily price</span>'
            f'<strong>{reference:.{decimals}f}</strong><span>{escape(unit)}</span>'
            f'<span>Observation date: {reference_date}</span>'+legend+'</aside></div>'
            '<p class="muted">Colors compare unrounded monthly means with the last available daily observation through the cutoff, '
            f'in the selected display units. Matrix prices and the reference use {decimals} decimal places; calculations and colors retain full precision. '
            '* Current calendar month is partial. — No data or month after cutoff (hover for the reason); '
            'counts appear on hover. Colors describe historical price levels, not buy/sell signals.</p>')


def _recent_year_chart(result, unit):
    colors = ('#93c5fd','#2563eb','#7c3aed','#0f766e','#c45d11','#111827')
    lines = [(str(year),result.monthly_means.loc[year],colors[i]) for i,year in enumerate(result.years)]
    lines.append(('Period average',result.mean_series,colors[-1]))
    values = [float(v) for _,row,_ in lines for v in row if not math.isnan(float(v))]
    if not values:
        return '<p>No observations in these five calendar years.</p>'
    scale,low,high,labels = _axis(values)
    left=max(76,max(len(label) for label in labels)*7+12)
    x=lambda m:left+(m-1)*(1040-left)/11
    y=lambda v:260-(float(v)/scale-low)/(high-low)*220
    svg=['<svg viewBox="0 0 1120 355" role="img" aria-label="Five calendar-year monthly average price lines including the current year, and period mean"><title>Monthly mean prices by year and equal-year period mean</title>',f'<text x="{left}" y="19">{escape(unit)}</text>']
    for i,label in enumerate(labels):
        yy=260-i*55
        svg.append(f'<line x1="{left}" x2="1040" y1="{yy}" y2="{yy}" stroke="#dce3ed"/><text x="{left-10}" y="{yy+4}" text-anchor="end">{escape(label)}</text>')
    for index,(name,row,color) in enumerate(lines):
        path='';opened=False;markers=[]
        for month,value in row.items():
            if math.isnan(float(value)):
                opened=False;continue
            path+=(' L ' if opened else ' M ')+f'{x(month):.3f},{y(value):.3f}';opened=True
            hollow=(name==str(result.as_of.year) and month==result.as_of.month
                    and result.as_of.day!=__import__('calendar').monthrange(result.as_of.year,month)[1])
            markers.append(f'<circle data-year-line="{index}" cx="{x(month):.3f}" cy="{y(value):.3f}" r="3" fill="{"#fff" if hollow else color}" stroke="{color}"/>')
        width='3.2' if index==5 else '2.2';dash=' stroke-dasharray="7 4"' if index==5 else ''
        svg.append(f'<path data-year-line="{index}" d="{path}" fill="none" stroke="{color}" stroke-width="{width}"{dash}/>'+''.join(markers))
        xx=left+(index%3)*310;yy=309+(index//3)*25
        svg.append(f'<line x1="{xx}" x2="{xx+25}" y1="{yy}" y2="{yy}" stroke="{color}" stroke-width="{width}"{dash}/><text x="{xx+34}" y="{yy+4}">{escape(name)}</text>')
    for month,name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'),1):
        svg.append(f'<text x="{x(month):.3f}" y="283" text-anchor="middle">{name}</text>')
    svg.append('</svg>')
    controls='<div class="checks">'+''.join(f'<label><input type="checkbox" data-year-toggle="{i}" checked> <span style="color:{color}">{escape(name)}</span></label>' for i,(name,_,color) in enumerate(lines))+'</div>'
    table=[]
    for month,name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'),1):
        table.append('<tr><th>'+name+'</th>'+''.join(f'<td title="{"Month after analysis cutoff" if year == result.as_of.year and month > result.as_of.month else "Monthly average; — means no observations"}">{_fmt(result.monthly_means.loc[year,month])}</td>' for year in result.years)+f'<td>{_fmt(result.mean_series.loc[month])}</td><td>{int(result.year_count.loc[month])}/5</td><td>{int(result.observation_count.loc[month])}</td></tr>')
    header='<tr><th>Month</th>'+''.join(f'<th>{year}</th>' for year in result.years)+'<th>Period average</th><th>Years used</th><th>Observations</th></tr>'
    return f'<h3>{result.years[0]}–{result.years[-1]} · {escape(unit)}</h3>'+controls+''.join(svg)+'<details><summary>Monthly values and coverage</summary><div class="table-wrap"><table><thead>'+header+'</thead><tbody>'+''.join(table)+'</tbody></table></div></details>'


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
    return '—' if value is None or math.isnan(float(value)) else format(float(value), '.6g')


def _heatmap(frame, *, as_of):
    frame = frame.copy()
    frame['year'] = frame.index.year
    frame['month'] = frame.index.month
    rows = []
    for year, group in frame.groupby('year'):
        cells = []
        for month in range(1, 13):
            item = group[group['month'] == month]
            if item.empty:
                future = year == as_of.year and month > as_of.month
                reason = 'Month after analysis cutoff' if future else 'No observations for this month'
                cells.append(f'<td class="{"future-month" if future else "missing"}" title="{reason}">—</td>')
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
    daily = technical_analysis(frame, as_of=as_of)
    axes = {}
    range_starts = {'12m':(pd.Timestamp(as_of)-pd.DateOffset(months=12)).date().isoformat(),
                    '90':(as_of-timedelta(days=90)).isoformat(),'all':None}
    for horizon,start in range_starts.items():
        visible = daily.frame if start is None else daily.frame[daily.frame.date.dt.date >= date.fromisoformat(start)]
        for mask in range(1,64):
            columns = [name for i,name in enumerate(TECHNICAL_COLUMNS) if mask & (1 << i)]
            values = [float(v) for name in columns for v in visible[name] if not math.isnan(float(v))]
            axes[horizon+':'+str(mask)] = _axis(values) if values else None
    profiles = [analyze_seasonality(frame, as_of=as_of, window_years=n) for n in (5, 10)]
    normalized = []
    bases = []
    for n in (5, 10):
        try:
            indexed = normalized_seasonality(frame, as_of=as_of, window_years=n)
            normalized.append(indexed.seasonal)
            display_bases = indexed.bases.copy()
            display_bases['base_date'] = display_bases['base_date'].map(lambda value: '—' if pd.isna(value) else value.isoformat()[:10])
            bases.append(f'<details><summary>{n}-year normalization bases</summary><div class="table-wrap">'+display_bases.to_html(escape=True,na_rep='—',border=0)+'</div></details>')
        except ValueError as exc:
            normalization_error = str(exc)
            break
    else:
        normalization_error = None
    try:
        returns = _heatmap(monthly_returns(frame, as_of=as_of).frame,as_of=as_of)
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
    return dict(daily=_records(daily.frame), axes=axes,range_starts=range_starts,
                price_matrix=_monthly_price_matrix(frame,as_of=as_of,unit=unit),
                fiveyear=_recent_year_chart(recent_year_prices(frame,as_of=as_of),unit),
                profiles=_sections(render_seasonal_report(profiles, unit=unit)),
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
