"""Standalone local HTML reports with SVG charts and inspectable tables."""

from calendar import month_abbr
from decimal import Decimal, localcontext
from html import escape
import math
import sys
from typing import Sequence

from .seasonal import SeasonalResult


def _number(value):
    return "Missing" if math.isnan(float(value)) else format(float(value), ".12g")


def _runs(points):
    """Split chart paths at missing months instead of connecting across gaps."""
    result, run = [], []
    for point in points:
        if point is None:
            if run:
                result.append(run)
                run = []
        else:
            run.append(point)
    if run:
        result.append(run)
    return result


def _chart_values(result):
    baseline, current = result.profile, result.current
    values = [float(v) for column in ("mean", "minimum", "maximum") for v in baseline[column] if not math.isnan(float(v))]
    values += [float(v) for v in current["mean"] if not math.isnan(float(v))]
    if any(not math.isfinite(v) for v in values):
        raise ValueError("Chart values must be finite or missing.")
    return values


def _axis(values):
    """Fit all plotted levels with padding, without forcing zero into the range."""
    # Normalize before subtraction to support finite values of opposite signs.
    scale = max(abs(v) for v in values) or 1.0
    low, high = min(v / scale for v in values), max(v / scale for v in values)
    if high == low:
        padding = 0.01 if low else 1.0
    else:
        padding = max((high - low) * 0.08, math.ulp(low), math.ulp(high))
    # At the largest float, the usual margin cannot be represented in input
    # units. Keep every axis label finite, even if that edge gets no margin.
    limit = sys.float_info.max / scale
    low, high = max(low - padding, -limit), min(high + padding, limit)
    # Decimal labels avoid collapsing subnormal tick values to the same float.
    # Geometry still uses normalized float64 coordinates.
    with localcontext() as context:
        context.prec = 40
        lower, upper, magnitude = map(Decimal.from_float, (low, high, scale))
        max_value = Decimal.from_float(sys.float_info.max)
        ticks = [max(-max_value, min(max_value, (lower + (upper - lower) * Decimal(i) / 4) * magnitude)) for i in range(5)]
        for precision in range(5, 21):
            labels = [format(v, f".{precision}g") for v in ticks]
            if (len(set(labels)) == len(set(ticks))
                    and all(math.isfinite(float(label)) for label in labels)
                    and float(labels[0]) <= min(values)
                    and float(labels[-1]) >= max(values)):
                break
    return scale, low, high, labels


def _chart(result, unit, axis):
    baseline, current = result.profile, result.current
    if not _chart_values(result):
        return '<p class="empty">No observations in this window or reference year.</p>'
    scale, low, high, labels = axis
    left = max(76, max(len(label) for label in labels) * 7 + 12)

    def x(month):
        return left + (month - 1) * (758 - left) / 11

    def y(value):
        return 238 - ((float(value) / scale - low) / (high - low)) * 202

    def line(values, color):
        points = [None if math.isnan(float(v)) else (x(m), y(v)) for m, v in enumerate(values, 1)]
        path = " ".join("M " + " L ".join(f"{a:.3f},{b:.3f}" for a, b in run) for run in _runs(points))
        return f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"/>'

    svg = [f'<svg viewBox="0 0 820 350" role="img" aria-label="{escape(str(result.window_years))}-year monthly profile and reference year">',
           '<title>Monthly levels, equal-year baseline and observed historical range</title>',
           '<desc>Auto-scaled Y-axis shared by the profiles in this report; zero is not forced. Missing months are gaps. Orange hollow markers indicate a calendar month in progress. Tables below contain values and coverage.</desc>']
    for i in range(5):
        yy = 238 - 202 * i / 4
        label = escape(labels[i])
        svg.append(f'<line x1="{left}" y1="{yy:.3f}" x2="758" y2="{yy:.3f}" stroke="#dce3ed"/><text x="{left - 10}" y="{yy + 4:.3f}" text-anchor="end">{label}</text>')
    band = [None if math.isnan(float(row.minimum)) else (x(m), y(row.minimum), y(row.maximum)) for m, row in baseline.iterrows()]
    for run in _runs(band):
        if len(run) == 1:
            xx, bottom, top = run[0]
            svg.append(f'<rect x="{xx - 5:.3f}" y="{top:.3f}" width="10" height="{bottom - top:.3f}" fill="#dbeafe"/>')
        else:
            polygon = [(p[0], p[2]) for p in run] + [(p[0], p[1]) for p in reversed(run)]
            coordinates = " ".join(f"{a:.3f},{b:.3f}" for a, b in polygon)
            svg.append(f'<polygon points="{coordinates}" fill="#dbeafe"/>')
    svg.extend([line(baseline["mean"], "#2563eb"), line(current["mean"], "#c45d11")])
    for month in range(1, 13):
        svg.append(f'<text x="{x(month)}" y="260" text-anchor="middle">{month_abbr[month]}</text>')
        for value, color, hollow in ((baseline.loc[month, "mean"], "#2563eb", False),
                                      (current.loc[month, "mean"], "#c45d11", current.loc[month, "calendar_status"] == "month_in_progress")):
            if not math.isnan(float(value)):
                fill = "#fff" if hollow else color
                svg.append(f'<circle cx="{x(month)}" cy="{y(value):.3f}" r="4" fill="{fill}" stroke="{color}" stroke-width="2"/>')
    svg.extend([
        f'<text x="76" y="17">{escape(unit)}</text>',
        '<g class="chart-legend" aria-label="Chart legend">',
        '<line x1="76" y1="286" x2="104" y2="286" stroke="#2563eb" stroke-width="2.5"/><circle cx="90" cy="286" r="3" fill="#2563eb"/>',
        f'<text x="112" y="290">{result.window_years}-year average ({result.start_year}–{result.end_year})</text>',
        '<line x1="330" y1="286" x2="358" y2="286" stroke="#c45d11" stroke-width="2.5"/><circle cx="344" cy="286" r="3" fill="#c45d11"/>',
        f'<text x="366" y="290">{result.as_of.year} monthly average</text>',
        '<rect x="560" y="280" width="28" height="12" fill="#dbeafe"/>',
        '<text x="596" y="290">Historical min–max</text>',
        '<text x="76" y="313">Shaded range: minimum–maximum of yearly monthly averages, not daily highs/lows.</text>',
        '<circle cx="82" cy="332" r="4" fill="#fff" stroke="#c45d11" stroke-width="2"/>',
        f'<text x="96" y="336">Hollow marker: partial month, through {result.as_of.isoformat()}.</text>',
        '</g></svg>',
    ])
    return "\n".join(svg)


def render_seasonal_report(
    results: Sequence[SeasonalResult],
    *,
    title: str = "SeasonLens — local seasonal analysis",
    unit: str = "Original input units",
    import_summary: dict[str, int] | None = None,
) -> str:
    """Render compatible results without writing a file or loading external assets.

    Statistics are input-unit monthly levels, not normalized returns. All table
    values display 12 significant digits. This is a private output when its
    input is private; rendering does not grant redistribution rights.
    """
    results = tuple(results)
    if not results or any(not isinstance(r, SeasonalResult) for r in results):
        raise ValueError("At least one SeasonalResult is required.")
    if not isinstance(title, str) or not isinstance(unit, str):
        raise ValueError("title and unit must be strings.")
    if len({r.window_years for r in results}) != len(results):
        raise ValueError("Profile windows must be distinct.")
    first = results[0]
    # Differences depend on each window; only compare source-year columns.
    if any(r.as_of != first.as_of or not r.current.drop(columns="difference").equals(first.current.drop(columns="difference")) or r.excluded_future_observations != first.excluded_future_observations for r in results):
        raise ValueError("Results must use the same reference date and current series.")
    plotted_values = [v for result in results for v in _chart_values(result)]
    axis = _axis(plotted_values) if plotted_values else None
    metadata = ""
    if import_summary is not None:
        for key, value in import_summary.items():
            if not isinstance(key, str) or not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("Import summary must contain text labels and nonnegative integer counts.")
        metadata = '<ul class="metadata">' + "".join(f'<li>{escape(k)}: <strong>{v}</strong></li>' for k, v in import_summary.items()) + '</ul>'
    sections = []
    statuses = {"month_ended": "Calendar month ended", "month_in_progress": "Partial calendar month", "after_cutoff": "After cutoff"}
    for result in results:
        rows = []
        for month in range(1, 13):
            p, c = result.profile.loc[month], result.current.loc[month]
            rows.append('<tr>' + f'<th scope="row">{month_abbr[month]}</th>' + ''.join(f'<td>{_number(v)}</td>' for v in (p["mean"], p["minimum"], p["maximum"])) + f'<td>{int(p.year_count)}/{result.window_years}</td><td>{int(p.observation_count)}</td>' + f'<td>{_number(c["mean"])}</td><td>{int(c.observation_count)}</td><td>{_number(c.difference)}</td><td>{statuses[c.calendar_status]}</td></tr>')
        header = ['Month', 'Baseline mean', 'Historical min', 'Historical max', 'Years used', 'Baseline observations', f'{result.as_of.year} mean', f'{result.as_of.year} observations', 'Difference', 'Calendar status']
        sections.append(f'<section><h2>{result.window_years}-year profile: {result.start_year}–{result.end_year}</h2><p>Blue: equal-year baseline. Orange: {result.as_of.year} through {result.as_of.isoformat()}. Pale blue: historical range of yearly monthly means.</p>' + _chart(result, unit, axis) + '<div class="table-wrap"><table><caption>Monthly values and observed coverage; displayed to 12 significant digits</caption><thead><tr>' + ''.join(f'<th scope="col">{h}</th>' for h in header) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></section>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f2f5fa;color:#172339;font:15px/1.5 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:28px 20px}}h1{{font-size:30px;margin:0 0 10px}}h2{{font-size:21px}}section{{background:white;padding:22px;border:1px solid #dce3ed;border-radius:12px;margin:22px 0}}.notice{{background:#fff5de;border-left:4px solid #d28a08;padding:12px 16px}}.metadata{{display:flex;gap:10px 28px;flex-wrap:wrap;padding-left:20px}}svg{{width:100%;height:auto;max-height:380px}}svg text{{font:12px system-ui,sans-serif;fill:#4b5d76}}.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:9px;border-bottom:1px solid #e4e9f1;text-align:right;white-space:nowrap}}th:first-child,td:last-child{{text-align:left}}thead{{background:#f2f5fa}}caption{{text-align:left;padding:12px 0;color:#52627a}}footer{{color:#52627a;font-size:13px}}@media(max-width:600px){{main{{padding:16px 10px}}section{{padding:14px}}h1{{font-size:24px}}}}@media print{{body{{background:white}}section{{break-inside:avoid}}main{{max-width:none}}}}
</style></head><body><main><h1>{escape(title)}</h1><p>Reference date: <strong>{first.as_of.isoformat()}</strong> · Units: {escape(unit)}</p>
<p class="notice">Historical monthly levels, not a forecast or normalized returns. Each available year has equal weight. Missing months stay missing. Calendar-ended months can still have missing trading sessions; a partial reference month is compared with full historical calendar months.</p>
{metadata}<p>Valid input observations after the reference date excluded from calculations: <strong>{first.excluded_future_observations}</strong>.</p>
<p>Y-axis: automatically fitted to the plotted levels with a small margin; zero is not forced. Both profile charts use the same scale for comparison.</p>
{''.join(sections)}<footer>Generated locally by SeasonLens. No external assets or network requests. Imported data and derived output retain their source restrictions. No inflation adjustment, futures roll correction, trading calendar or interpolation is applied.</footer></main></body></html>'''
